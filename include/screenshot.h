#pragma once
#include <d3d11.h>
#include <dxgi.h>
#include <dxgi1_2.h>
#include <Windows.h>
#include <wincodec.h>

static int screenWidth = 2560; // 屏幕宽度
static int screenHeight = 1600; // 屏幕高度
static int cropSize = 640; // 裁剪区域大小

bool CaptureScreenRegion(RECT captureRect, 
        IDXGIOutputDuplication* duplication, ID3D11Device* device, ID3D11DeviceContext* context, 
        BYTE** dst, ID3D11Texture2D* stagingTex);

bool Init_D3D(ID3D11Device*& device, ID3D11DeviceContext*& context, IDXGIOutputDuplication*& duplication, 
    ID3D11Texture2D*& stagingTex);
