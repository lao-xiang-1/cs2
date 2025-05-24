# cs2辅助瞄准工具

主要思路：
1.截图取屏幕中心640*640的图像
2.基于yolov11处理图像，获取敌人位置
3.根据识别结果移动准心

环境搭建：
主要就是配yolov11的环境，其他还有一些依赖库可自行看代码安装
yolov11源码地址：https://github.com/ultralytics/ultralytics
搭建教程：https://www.bilibili.com/video/BV1xgcLeLE7a/?spm_id_from=333.337.search-card.all.click&vd_source=7a246f3599c93bd9ab74f15842ec7bec

由于cs2反作弊机制的影响，游戏过程中一般的Windows api无法移动准心，这里用了罗技鼠标宏，需先下载软件
下载地址：https://pan.baidu.com/s/1UuvGDVMzrZKtE8NtYYgIGQ 提取码: 0721

记得修改logi.py文件中dll的路径，根据下载路径改为实际存在的绝对路径

使用方法：
环境搭好之后运行cs2.py
可选择攻击对象
按/选择攻击头或身体
按*选择攻击T或CT
按-选择开启或关闭自动开火
按+选择是否暂停
按=结束（实际可能还需按一下+）

实际使用情况：
游戏中可能无法使用热键功能，需按一下win键进入开始菜单再按
模型效果一般，可能会有误识别的情况，在一些地图上尤为明显

宇宙安全声明：
本项目仅供学习交流使用，我坚决反对使用外挂破坏游戏公平等行为，开发过程中所做的测试仅在人机对局中进行
