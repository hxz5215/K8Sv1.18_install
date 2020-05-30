# K8Sv1.18_install
执行脚本，一键安装


#前置准备工作,非常重要，否则将安装失败

1、检查各服务器是否能连接网络，并且以一台作为节点对剩下服务器做免密登录

2、安装python3、git
```
yum -y install python36  git
```

3、下载脚本
> " ~/K8Sv1.18_install" 这个值 为存放到本地路径的值
```
git clone https://github.com/hxz5215/K8Sv1.18_install.git ~/K8Sv1.18_install
```

4、 安装paramiko 模块，网络不好可能会安装失败，如果失败重复几次即可
```
pip3 install paramiko
```

5、执行脚本，一键安装K8S V1.18

```
python3 ~/K8Sv1.18_install/k8s_install.py
```

备注：
>1:初始化过程中有大量工作，请耐心等待，不要强制结束

>2:如果遇到异常情况脚本退出，也请将你的环境回归到初始状态

>3:多Master的高可用集群暂时还没有写出来
