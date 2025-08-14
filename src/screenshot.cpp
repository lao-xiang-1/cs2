#include <Windows.h>
#include <dxgi.h>
#include <dxgi1_2.h>
#include <d3d11.h>
#include <wincodec.h>
#include <vector>
#include <cstdio>
#include <iostream>
#include <string>
#include <opencv2/opencv.hpp>
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "dxgi.lib")

static int screenWidth = 2560; // 屏幕宽度
static int screenHeight = 1600; // 屏幕高度
static int cropSize = 640; // 裁剪区域大小

// 安全释放 COM 对象
template<typename T>
void SafeRelease(T*& ptr) {
    if (ptr) {
        ptr->Release();
        ptr = nullptr;
    }
}

bool CaptureScreenRegion(RECT captureRect, 
        IDXGIOutputDuplication* duplication, ID3D11Device* device, ID3D11DeviceContext* context, 
        BYTE** dst, ID3D11Texture2D* stagingTex) {

    // 4. 捕获帧
    DXGI_OUTDUPL_FRAME_INFO frameInfo;
    IDXGIResource* desktopResource = nullptr;
    HRESULT hr = duplication->AcquireNextFrame(500, &frameInfo, &desktopResource);
    if (FAILED(hr)) {
        duplication->ReleaseFrame();
        SafeRelease(desktopResource);
        std::cout << "Failed to acquire next frame." << std::endl;
        return false;
    }
    if (frameInfo.TotalMetadataBufferSize == 0) {
        std::cout << "No metadata available, skipping frame." << std::endl;
        duplication->ReleaseFrame();
        SafeRelease(desktopResource);
        return false;
    }

    // 5. 获取桌面纹理接口
    ID3D11Texture2D* desktopTexture = nullptr;
    desktopResource->QueryInterface(__uuidof(ID3D11Texture2D), (void**)&desktopTexture);

    context->CopyResource(stagingTex, desktopTexture);

    // 6. 映射纹理数据
    D3D11_MAPPED_SUBRESOURCE mapInfo;
    hr = context->Map(stagingTex, 0, D3D11_MAP_READ, 0, &mapInfo);
    // 7. 裁剪目标区域
    int width = captureRect.right - captureRect.left;
    int height = captureRect.bottom - captureRect.top;
    
    BYTE* src = (BYTE*)mapInfo.pData;
    
    // 计算偏移 (目标区域左上角)
    int startX = captureRect.left;
    int startY = captureRect.top;
    
    for (int y = 0; y < height; y++) {
        BYTE* srcRow = src + ((startY + y) * mapInfo.RowPitch) + (startX * 4);
        memcpy((*dst) + (y * width * 4), srcRow, width * 4);
    }
    // 9. 清理资源
    SafeRelease(desktopTexture);
    SafeRelease(desktopResource);

    return true;
}

bool Init_D3D(ID3D11Device*& device, ID3D11DeviceContext*& context, IDXGIOutputDuplication*& duplication, ID3D11Texture2D*& stagingTex)
{
    // 1. 初始化 D3D
    D3D_FEATURE_LEVEL featureLevel;
    if (FAILED(D3D11CreateDevice(
        nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0, 
        nullptr, 0, D3D11_SDK_VERSION, 
        &device, &featureLevel, &context))) 
    {
        std::cout << "1" << std::endl;
        return false;
    }

    // 2. 获取输出适配器
    IDXGIDevice* dxgiDevice = nullptr;
    device->QueryInterface(__uuidof(IDXGIDevice), (void**)&dxgiDevice);
    
    IDXGIAdapter* adapter = nullptr;
    dxgiDevice->GetAdapter(&adapter);
    
    IDXGIOutput* output = nullptr;
    adapter->EnumOutputs(0, &output); // 获取第一个显示器
    
    IDXGIOutput1* output1 = nullptr;
    output->QueryInterface(__uuidof(IDXGIOutput1), (void**)&output1);

    // 3. 创建桌面复制对象
    DXGI_OUTDUPL_DESC dupDesc;
    if (FAILED(output1->DuplicateOutput(device, &duplication))) {
        SafeRelease(output1);
        SafeRelease(output);
        SafeRelease(adapter);
        SafeRelease(dxgiDevice);
        SafeRelease(context);
        SafeRelease(device);
        std::cout << "2" << std::endl;
        return false;
    }

    // 获取帧
    DXGI_OUTDUPL_FRAME_INFO frameInfo;
    IDXGIResource* desktopResource = nullptr;
    if (FAILED(duplication->AcquireNextFrame(0, &frameInfo, &desktopResource))) {
        duplication->ReleaseFrame();
        SafeRelease(duplication);
        std::cout << "please run with administrator privileges." << std::endl;
        return false;
    }

    // 跳过坏帧
    for (int i = 0; i < 10; ++i) {
        if (frameInfo.TotalMetadataBufferSize > 0) {
            break;
        }else{
            duplication->ReleaseFrame();
        }
        Sleep(10); // 等待一段时间后重试
        HRESULT hr = duplication->AcquireNextFrame(500, &frameInfo, &desktopResource);
        if (FAILED(hr)) {
            duplication->ReleaseFrame();
            SafeRelease(desktopResource);
            SafeRelease(duplication);
        }
    }

    ID3D11Texture2D* desktopTexture = nullptr;
    desktopResource->QueryInterface(__uuidof(ID3D11Texture2D), (void**)&desktopTexture);
    
    // 5. 创建暂存纹理 (CPU可读)
    D3D11_TEXTURE2D_DESC texDesc;
    desktopTexture->GetDesc(&texDesc);
    texDesc.BindFlags = 0;
    texDesc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    texDesc.Usage = D3D11_USAGE_STAGING;
    texDesc.MiscFlags = 0;

    device->CreateTexture2D(&texDesc, nullptr, &stagingTex);

    duplication->ReleaseFrame();

    SafeRelease(output1);
    SafeRelease(output);
    SafeRelease(adapter);
    SafeRelease(dxgiDevice);
    
    return true;
}
