
#include <fstream>
#include <iostream>
#include <opencv2/opencv.hpp>
#include "cuda_utils.h"
#include "logging.h"
#include "model.h"
#include "postprocess.h"
#include "preprocess.h"
#include "utils.h"
#include "screenshot.h"
#include "mouse.h"
#include "pid.h"
#include "json.hpp"

struct Config{
    int Head_body = 0;
    int CT_T = 1;
    int Auto_fire = 0;
    NLOHMANN_DEFINE_TYPE_INTRUSIVE(Config, Head_body, CT_T, Auto_fire);
};

Logger gLogger;
using namespace nvinfer1;
const int kOutputSize = kMaxNumOutputBbox * sizeof(Detection) / sizeof(float) + 1;

// 安全释放 COM 对象
template<typename T>
void SafeRelease(T*& ptr) {
    if (ptr) {
        ptr->Release();
        ptr = nullptr;
    }
}

void deserialize_engine(std::string& engine_name, IRuntime** runtime, ICudaEngine** engine,
                        IExecutionContext** context) {
    std::ifstream file(engine_name, std::ios::binary);
    if (!file.good()) {
        std::cerr << "read " << engine_name << " error!" << std::endl;
        assert(false);
    }
    size_t size = 0;
    file.seekg(0, file.end);
    size = file.tellg();
    file.seekg(0, file.beg);
    char* serialized_engine = new char[size];
    assert(serialized_engine);
    file.read(serialized_engine, size);
    file.close();

    *runtime = createInferRuntime(gLogger);
    assert(*runtime);
    *engine = (*runtime)->deserializeCudaEngine(serialized_engine, size);
    assert(*engine);
    *context = (*engine)->createExecutionContext();
    assert(*context);
    delete[] serialized_engine;
}

void prepare_buffer(ICudaEngine* engine, float** input_buffer_device, float** output_buffer_device,
                    float** output_buffer_host, float** decode_ptr_host, float** decode_ptr_device,
                    std::string cuda_post_process) {
    assert(engine->getNbBindings() == 2);
    // In order to bind the buffers, we need to know the names of the input and output tensors.
    // Note that indices are guaranteed to be less than IEngine::getNbBindings()
    const int inputIndex = engine->getBindingIndex(kInputTensorName);
    const int outputIndex = engine->getBindingIndex(kOutputTensorName);
    assert(inputIndex == 0);
    assert(outputIndex == 1);
    // Create GPU buffers on device
    CUDA_CHECK(cudaMalloc((void**)input_buffer_device, kBatchSize * 3 * kInputH * kInputW * sizeof(float)));
    CUDA_CHECK(cudaMalloc((void**)output_buffer_device, kBatchSize * kOutputSize * sizeof(float)));
    if (cuda_post_process == "c") {
        *output_buffer_host = new float[kBatchSize * kOutputSize];
    } else if (cuda_post_process == "g") {
        if (kBatchSize > 1) {
            std::cerr << "Do not yet support GPU post processing for multiple batches" << std::endl;
            exit(0);
        }
        // Allocate memory for decode_ptr_host and copy to device
        *decode_ptr_host = new float[1 + kMaxNumOutputBbox * bbox_element];
        CUDA_CHECK(cudaMalloc((void**)decode_ptr_device, sizeof(float) * (1 + kMaxNumOutputBbox * bbox_element)));
    }
}

void infer(IExecutionContext& context, cudaStream_t& stream, void** buffers, float* output, int batchsize,
           float* decode_ptr_host, float* decode_ptr_device, int model_bboxes, std::string cuda_post_process) {
    // infer on the batch asynchronously, and DMA output back to host
    auto start = std::chrono::system_clock::now();
    context.enqueue(batchsize, buffers, stream, nullptr);
    if (cuda_post_process == "c") {
        CUDA_CHECK(cudaMemcpyAsync(output, buffers[1], batchsize * kOutputSize * sizeof(float), cudaMemcpyDeviceToHost,
                                   stream));
        auto end = std::chrono::system_clock::now();
        std::cout << "inference time: " << std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count()
                  << "ms" << std::endl;
    } else if (cuda_post_process == "g") {
        CUDA_CHECK(
                cudaMemsetAsync(decode_ptr_device, 0, sizeof(float) * (1 + kMaxNumOutputBbox * bbox_element), stream));
        cuda_decode((float*)buffers[1], model_bboxes, kConfThresh, decode_ptr_device, kMaxNumOutputBbox, stream);
        cuda_nms(decode_ptr_device, kNmsThresh, kMaxNumOutputBbox, stream);  //cuda nms
        CUDA_CHECK(cudaMemcpyAsync(decode_ptr_host, decode_ptr_device,
                                   sizeof(float) * (1 + kMaxNumOutputBbox * bbox_element), cudaMemcpyDeviceToHost,
                                   stream));
        auto end = std::chrono::system_clock::now();
        std::cout << "inference and gpu postprocess time: "
                  << std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count() << "ms" << std::endl;
    }

    CUDA_CHECK(cudaStreamSynchronize(stream));
}

bool parse_args(int argc, char** argv, std::string& engine, std::string& cuda_post_process) {
    if (argc < 3)
        return false;
    if (std::string(argv[1]) == "-d" && argc == 4) {
        engine = std::string(argv[2]);
        cuda_post_process = std::string(argv[3]);
    } else {
        return false;
    }
    return true;
}

bool read_enemy_config(std::string cfg_pth) {
    std::ifstream config_is(cfg_pth, std::ios::in);
    if (!config_is.good()) {
        std::cerr << "the config path is wrong!" << std::endl;
        config_is.close();
        return false;
    }

    nlohmann::json cfg_json;
    config_is >> cfg_json;
    config_is.close();
    Config cfg;
    try
    {
        cfg = cfg_json.get<Config>();
    }
    catch (const nlohmann::detail::exception &e)
    {
        std::cerr << "Json Params Parse failed :" << e.what() << '\n';
        return false;
        exit(-1);
    }

    Head_body = cfg.Head_body;
    CT_T = cfg.CT_T;
    Auto_fire = cfg.Auto_fire; 
    return true;
}

int main(int argc, char** argv) {
    if (!read_enemy_config("config\\enemy_config.json")){
        std::cerr << "Failed to read enemy configuration." << std::endl;
        return -1;
    }
    cudaSetDevice(kGpuId);
    std::string engine_name = "yolov8s_cs2_net.engine";
    std::string cuda_post_process = "g";
    int model_bboxes;

    //if (!parse_args(argc, argv, engine_name, cuda_post_process)) {
    //    std::cerr << "Arguments not right!" << std::endl;
    //    std::cerr << "./yolov8 -d [.engine] ../samples  [c/g]// deserialize plan file and run inference" << std::endl;
    //    return -1;
    //}

    // Deserialize the engine from file
    IRuntime* runtime = nullptr;
    ICudaEngine* engine = nullptr;
    IExecutionContext* context = nullptr;
    deserialize_engine(engine_name, &runtime, &engine, &context);
    cudaStream_t stream;
    CUDA_CHECK(cudaStreamCreate(&stream));
    cuda_preprocess_init(kMaxInputImageSize);
    auto out_dims = engine->getBindingDimensions(1);
    model_bboxes = out_dims.d[0];
    // Prepare cpu and gpu buffers
    float* device_buffers[2];
    float* output_buffer_host = nullptr;
    float* decode_ptr_host = nullptr;
    float* decode_ptr_device = nullptr;

    prepare_buffer(engine, &device_buffers[0], &device_buffers[1], &output_buffer_host, &decode_ptr_host,
                &decode_ptr_device, cuda_post_process);

    // initialize the screenshot capture
    RECT captureArea = { screenWidth / 2 - cropSize / 2, screenHeight / 2 - cropSize / 2, 
        screenWidth / 2 + cropSize / 2, screenHeight / 2 + cropSize / 2 };

    ID3D11Device* Dx_device = nullptr;
    ID3D11DeviceContext* Dx_context = nullptr;
    IDXGIOutputDuplication* Dx_duplication = nullptr;
    ID3D11Texture2D* Dx_stagingTex = nullptr;
    BYTE* dst = new BYTE[cropSize * cropSize * 4]; // ??????

    if (!Init_D3D(Dx_device, Dx_context, Dx_duplication, Dx_stagingTex)) {
        std::cout << "Failed to initialize D3D." << std::endl;
        return -1;
    }

    //initialize mouse control
    HMODULE hDll = LoadLibraryW(L"logitech.driver.dll");

    if (!check_dll(hDll)) {
            std::cerr << "DLL check failed" << std::endl;
            return -1;
        }

    cv::Mat bgrMat;

    pid_type_def pid_x, pid_y;
    const fp32 PID[3] = {1, 0, 0.01}; // pid argument
    PID_init(&pid_x, PID_POSITION, PID, 1000, 3);
    PID_init(&pid_y, PID_POSITION, PID, 1000, 3);

    // batch predict
    while (true) {
        auto startTime = GetTickCount64();
        // Capture the screen region
        if (CaptureScreenRegion(captureArea, Dx_duplication, Dx_device, Dx_context, &dst, Dx_stagingTex)) {
            Dx_duplication->ReleaseFrame();
            Dx_context->Unmap(Dx_stagingTex, 0);
            cv::Mat bgraMat(cropSize, cropSize, CV_8UC4, dst); // ?? BGRA ??
            cv::cvtColor(bgraMat, bgrMat, cv::COLOR_BGRA2BGR); // ????
        }else continue;
        // Get a batch of images
        std::vector<cv::Mat> img_batch;
        cv::Mat img = bgrMat.clone(); // Clone the captured image
        img_batch.push_back(img);
        // Preprocess
        cuda_batch_preprocess(img_batch, device_buffers[0], kInputW, kInputH, stream);
        // Run inference
        infer(*context, stream, (void**)device_buffers, output_buffer_host, kBatchSize, decode_ptr_host,
              decode_ptr_device, model_bboxes, cuda_post_process);
        std::vector<std::vector<Detection>> res_batch;
        if (cuda_post_process == "c") {
            // NMS
            batch_nms(res_batch, output_buffer_host, img_batch.size(), kOutputSize, kConfThresh, kNmsThresh);
        } else if (cuda_post_process == "g") {
            //Process gpu decode and nms results
            batch_process(res_batch, decode_ptr_host, img_batch.size(), bbox_element, img_batch);
        }
        Enemy enemy;
        int center[4] = {0};
        // Get enemy info
        get_enemy_info(img_batch, res_batch, enemy);
        if (CT_T == 0) {
            if (Head_body == 0) {
                if (enemy.CT_head_count > 0) {
                    center[0] = enemy.CT_head[0];
                    center[1] = enemy.CT_head[1];
                    center[2] = enemy.CT_head[2];
                    center[3] = enemy.CT_head[3];
                } else if (enemy.CT_count > 0) {
                    center[0] = enemy.CT[0];
                    center[1] = enemy.CT[1];
                    center[2] = enemy.CT[2];
                    center[3] = enemy.CT[3];
                }
            }else if (Head_body == 1) {
                if (enemy.CT_count > 0) {
                    center[0] = enemy.CT[0];
                    center[1] = enemy.CT[1];
                    center[2] = enemy.CT[2];
                    center[3] = enemy.CT[3];
                } else if (enemy.CT_head_count > 0) {
                    center[0] = enemy.CT_head[0];
                    center[1] = enemy.CT_head[1];
                    center[2] = enemy.CT_head[2];
                    center[3] = enemy.CT_head[3];
                }
            }
        }else if (CT_T == 1) {
            if (Head_body == 0) {
                if (enemy.T_head_count > 0) {
                    center[0] = enemy.T_head[0];
                    center[1] = enemy.T_head[1];
                    center[2] = enemy.T_head[2];
                    center[3] = enemy.T_head[3];
                } else if (enemy.T_count > 0) {
                    center[0] = enemy.T[0];
                    center[1] = enemy.T[1];
                    center[2] = enemy.T[2];
                    center[3] = enemy.T[3];
                }
            }else if (Head_body == 1) {
                if (enemy.T_count > 0) {
                    center[0] = enemy.T[0];
                    center[1] = enemy.T[1];
                    center[2] = enemy.T[2];
                    center[3] = enemy.T[3];
                } else if (enemy.CT_head_count > 0) {
                    center[0] = enemy.T_head[0];
                    center[1] = enemy.T_head[1];
                    center[2] = enemy.T_head[2];
                    center[3] = enemy.T_head[3];
                }
            }
        }
         int x = PID_calc(&pid_x, float(center[0]));
         int y = PID_calc(&pid_y, float(center[1]));
        if (center[0] != 0 || center[1] != 0) {
            moveR(x, y, 1);
            Sleep(10); // wait for the move to complete
            if (Auto_fire == 1 && abs(center[0]) < center[2] * 0.35 && abs(center[1]) < center[3] * 0.35) {
                if (center[0] != 0 && center[1] != 0) {
                    mouse_down(1);
                    Sleep(5); // Hold the mouse button for 10 ms
                    mouse_up(1);
                }
            }
        }
        auto endTime = GetTickCount64();
        std::cout << ". Capture time: " << (endTime - startTime) << " ms" << std::endl;
        // Draw bounding boxes
        draw_bbox(img_batch, res_batch);
        // Save images
        cv::imshow("_.jpg", img_batch[0]);
        int key = cv::waitKey(1);
        if (key == 27 || key == 'q' || key == 'Q') {
            break;
        }
    }

    device_close();
    FreeLibrary(hDll);
    cv::destroyAllWindows();
    // Release stream and buffers
    cudaStreamDestroy(stream);
    CUDA_CHECK(cudaFree(device_buffers[0]));
    CUDA_CHECK(cudaFree(device_buffers[1]));
    CUDA_CHECK(cudaFree(decode_ptr_device));
    delete[] decode_ptr_host;
    delete[] output_buffer_host;
    cuda_preprocess_destroy();
    // Destroy the engine
    delete context;
    delete engine;
    delete runtime;

    delete[] dst; // release buffer
    SafeRelease(Dx_duplication);
    SafeRelease(Dx_context);
    SafeRelease(Dx_device);

    // Print histogram of the output distribution
    //std::cout << "\nOutput:\n\n";
    //for (unsigned int i = 0; i < kOutputSize; i++)
    //{
    //    std::cout << prob[i] << ", ";
    //    if (i % 10 == 0) std::cout << std::endl;
    //}
    //std::cout << std::endl;

    return 0;
}
