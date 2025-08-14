#include <cstdint>

typedef float fp32;

#define PID_POSITION 0
#define PID_DELTA 1

#define LimitMax(input, max)   \
    {                          \
        if (input > max)       \
        {                      \
            input = max;       \
        }                      \
        else if (input < -max) \
        {                      \
            input = -max;      \
        }                      \
    }

typedef struct
{
    //PID运算模式
    uint8_t mode;
    //PID 三个基本参数
    fp32 Kp;
    fp32 Ki;
    fp32 Kd;

    int max_out;  //PID最大输出
    fp32 max_iout; //PID最大积分输出

    int out;		//三项叠加输出
    fp32 Pout;		//比例项输出
    fp32 Iout;		//积分项输出
    fp32 Dout;		//微分项输出
    //微分项最近三个值 0最新 1上一次 2上上次
    fp32 Dbuf[3];  
    //误差项最近三个值 0最新 1上一次 2上上次
    fp32 error[3];  

} pid_type_def;

void PID_init(pid_type_def *pid, uint8_t mode, const fp32 PID[3], int max_out, fp32 max_iout)
{
    if (pid == NULL || PID == NULL)
    {
        return;
    }
    pid->mode = mode;
    pid->Kp = PID[0];
    pid->Ki = PID[1];
    pid->Kd = PID[2];
    pid->max_out = max_out;
    pid->max_iout = max_iout;
    pid->Dbuf[0] = pid->Dbuf[1] = pid->Dbuf[2] = 0.0f;
    pid->error[0] = pid->error[1] = pid->error[2] = pid->Pout = pid->Iout = pid->Dout = pid->out = 0.0f;
}

int PID_calc(pid_type_def *pid, fp32 error)
{
    //判断传入的PID指针不为空
    if (pid == NULL)
    {
        return 0;
    }
    //存放过去两次计算的误差值
    pid->error[2] = pid->error[1];
    pid->error[1] = pid->error[0];
    // set the error
    pid->error[0] = error;
    //判断PID设置的模式
    if (pid->mode == PID_POSITION)
    {
        //位置式PID
        //比例项计算输出
        pid->Pout = pid->Kp * pid->error[0];
        //积分项计算输出
        pid->Iout += pid->Ki * pid->error[0];
        //存放过去两次计算的微分误差值
        pid->Dbuf[2] = pid->Dbuf[1];
        pid->Dbuf[1] = pid->Dbuf[0];
        //当前误差的微分用本次误差减去上一次误差来计算
        pid->Dbuf[0] = (pid->error[0] - pid->error[1]);
        //微分项输出
        pid->Dout = pid->Kd * pid->Dbuf[0];
        //对积分项进行限幅
        LimitMax(pid->Iout, pid->max_iout);
        //叠加三个输出到总输出
        pid->out = int(pid->Pout + pid->Iout + pid->Dout);
        //对总输出进行限幅
        LimitMax(pid->out, pid->max_out);
    }
    else if (pid->mode == PID_DELTA)
    {
        //增量式PID
        //以本次误差与上次误差的差值作为比例项的输入带入计算
        pid->Pout = pid->Kp * (pid->error[0] - pid->error[1]);
        //以本次误差作为积分项带入计算
        pid->Iout = pid->Ki * pid->error[0];
        //迭代微分项的数组
        pid->Dbuf[2] = pid->Dbuf[1];
        pid->Dbuf[1] = pid->Dbuf[0];
        //以本次误差与上次误差的差值减去上次误差与上上次误差的差值作为微分项的输入带入计算
        pid->Dbuf[0] = (pid->error[0] - 2.0f * pid->error[1] + pid->error[2]);
        pid->Dout = pid->Kd * pid->Dbuf[0];
        //叠加三个项的输出作为总输出
        pid->out += int(pid->Pout + pid->Iout + pid->Dout);
        //对总输出做一个先限幅
        LimitMax(pid->out, pid->max_out);
	}
	return pid->out;
}


