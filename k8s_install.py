#!/bin/python3
# -*- coding:utf-8 -*-
# author: Huxuezheng
# describe: K8S V1.18 一键脚本安装
import os
import subprocess


class k8s_install(object):
    def __init__(self,masterip,nodeip):
        self.masterip = masterip
        self.nodeip = nodeip

    def initialization_shell(self): #环境初始化shell
        # 关闭防火墙
        setenforce = "setenforce  0"
        sed_selinux = "sed -i 's/^SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux"
        sed_selinux1 = "sed -i 's/^SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config"
        sed_selinux2 = "sed -i 's/^SELINUX=permissive/SELINUX=disabled/g' /etc/sysconfig/selinux"
        sed_selinux3 = "sed -i 's/^SELINUX=permissive/SELINUX=disabled/g' /etc/selinux/config"
        stop_firewalld = "systemctl stop firewalld"
        disable_firewalld = "systemctl disable firewalld"
        swapoff_a = "swapoff -a"
        sed_swapoff = "sed -i 's/.*swap.*/#&/' /etc/fstab"

        #在所有服务器配置国内yum源
        yum_install = "yum install -y wget yum-utils device-mapper-persistent-data lvm2 ipset ipvsadm chrony git> /dev/null 2>&1"
        mkdir_repo = "mkdir /etc/yum.repos.d/bak && mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/bak > /dev/null 2>&1"
        wget_centos = "wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.cloud.tencent.com/repo/centos7_base.repo > /dev/null 2>&1"
        wget_epel = "wget -O /etc/yum.repos.d/epel.repo http://mirrors.cloud.tencent.com/repo/epel-7.repo > /dev/null 2>&1"
        wget_docker = "wget https://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo -O /etc/yum.repos.d/docker-ce.repo > /dev/null 2>&1"


        kubernetes_repo = """
cat >  /etc/yum.repos.d/kubernetes.repo << EOF
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://mirrors.aliyun.com/kubernetes/yum/doc/yum-key.gpg https://mirrors.aliyun.com/kubernetes/yum/doc/rpm-package-key.gpg
EOF
"""

        yum_clean = "yum -y makecache > /dev/null 2>&1"
        yum_makecahe = "yum -y makecache > /dev/null 2>&1"
        #修改内核参数，由于ipvs已经加入到了内核的主干，所以为kube-proxy开启ipvs的前提需要加载以下的内核模块
        modprobe_netfilter = "modprobe br_netfilter"
        br_netfilter = "echo 'br_netfilter' > /etc/modules-load.d/br_netfilter.conf"

        k8s_conf = """
cat > /etc/sysctl.d/k8s.conf <<EOF 
net.bridge.bridge-nf-call-ip6tables = 1 
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
vm.swappiness=0
EOF
"""

        limits_conf = """
cat > /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 65536
* hard nproc 65536
* soft  memlock  unlimited
* hard memlock  unlimited
DefaultLimitNOFILE=102400
DefaultLimitNPROC=102400
EOF
"""
        sysctl_k8s = "sysctl -p /etc/sysctl.d/k8s.conf > /dev/null 2>&1"

        #时间同步
        enable_chronyd = "systemctl enable chronyd.service"
        start_chronyd = "systemctl start chronyd.service"
        set_timezone = "timedatectl set-timezone Asia/Shanghai"
        ntpdate = "ntpdate ntp1.aliyun.com > /dev/null 2>&1"
        chronyc_sources = "chronyc sources > /dev/null 2>&1"

        #安装docker,kubelet
        remove_docker = "yum remove -y docker docker-ce docker-common docker-selinux docker-engine > /dev/null 2>&1"
        install_docker = "yum install -y docker-ce-19.03.5-3.el7.x86_64 > /dev/null 2>&1"
        start_docker = "systemctl start docker > /dev/null 2>&1"


        docker_reload = "systemctl daemon-reload > /dev/null 2>&1"
        enable_docker = "systemctl enable docker  > /dev/null 2>&1"
        restart_docker = "systemctl restart docker > /dev/null 2>&1"

        install_kubelet = "yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes > /dev/null 2>&1"
        enable_kubelet = "systemctl enable kubelet > /dev/null 2>&1"
        start_kubelet = "systemctl start kubelet > /dev/null 2>&1"
        return setenforce,sed_selinux,sed_selinux1,sed_selinux2,sed_selinux3,stop_firewalld,disable_firewalld,swapoff_a,sed_swapoff,yum_install,\
               mkdir_repo,wget_centos,wget_epel,wget_docker,kubernetes_repo,yum_clean,yum_makecahe,modprobe_netfilter,br_netfilter,k8s_conf,limits_conf,\
               sysctl_k8s,enable_chronyd,start_chronyd,set_timezone,ntpdate,chronyc_sources,remove_docker,install_docker,start_docker,docker_reload,enable_docker,restart_docker,\
               install_kubelet,enable_kubelet,start_kubelet

    def shell_command(self):
        masterip_list = self.masterip.split(',')
        nodeip_list = self.nodeip.split(',')
        token_creat = ()
        token_code = ()
        name_num = 0
        # #自动添加策略，保存服务器的主机名和密钥信息，如果不添加，那么不再本地know_hosts文件中记录的主机将无法连接
        for masterip in masterip_list:
            name_num += 1
            if masterip == masterip_list[0]:  # 如果是当前单节点
                docker_speed = """
cat > /etc/docker/daemon.json << EOF
{  
  \"exec-opts\": [\"native.cgroupdriver=systemd\"],
  \"registry-mirrors\": [\"https://q2hy3fzi.mirror.aliyuncs.com\"], 
  \"graph\": \"/tol/docker-data\" 
} 
EOF
"""
                print("*"*20,"进入Master节点操作，当前IP: %s" %masterip)
                master_name = "master0%s" % name_num
                #设置名字
                hostname = os.system("hostname %s"%master_name)
                etc_hostname =  os.system("echo '%s' > /etc/hostname" % master_name)
                #设置hosts
                master_host = masterip + "  " + master_name
                etc_hosts = os.system("echo '%s' >> /etc/hosts" % master_host)
                docker_speed = os.system(docker_speed)
                for hosts in nodeip_list:
                    name_num += 1
                    hosts_name = hosts + "  node0%s" % (name_num - 1)
                    node_hosts = os.system("echo '%s' >> /etc/hosts" % hosts_name)
                    scp_hosts = os.system("scp -rp /etc/hosts %s:/etc/hosts"%hosts)
                scp_hosts = os.system("scp -rp /etc/hosts %s:/etc/hosts" % nodeip_list[0])
                print("*"*20,"进入环境初始化，请耐心等待....")
                for shell in self.initialization_shell():
                    env_init = os.system(shell)
                print("*"*20,"环境初始化完成，安装kubeadm...")
                #设置hosts
                #集群初始化
                kubeadm_init = os.system("kubeadm init --kubernetes-version=1.18.0 --image-repository registry.aliyuncs.com/google_containers  --service-cidr=10.10.0.0/16 --pod-network-cidr=10.122.0.0/16 --apiserver-advertise-address=%s" % masterip)
                mkdir_kube = os.system("mkdir -p /root/.kube")
                kube_config = os.system("cp -i /etc/kubernetes/admin.conf /root/.kube/config")

                #部署calico
                print("*" * 20, "正在安装calico....")
                k8s_calico = os.system("git clone https://github.com/hxz5215/calico.git /etc/kubernetes/calico")
                apply_rbac = os.system("kubectl apply -f /etc/kubernetes/calico/rbac-kdd.yaml > /dev/null 2>&1")
                calico_apply = os.system("kubectl apply -f /etc/kubernetes/calico/calico.yaml > /dev/null 2>&1" )
                print("*" * 20, "calico安装完成....")
                token_creat = subprocess.getstatusoutput("kubeadm token create")
                token_code = subprocess.getstatusoutput("openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | openssl dgst -sha256 -hex | sed 's/^.* //'")

                #部署UI
                print("*" * 20, "正在安装dashboard....")
                k8s_dashboard =os.system("git clone https://github.com/hxz5215/k8s-dashboard-v2.0.0-beta8.git /etc/kubernetes/dashboard")
                recommended = os.system("kubectl apply -f /etc/kubernetes/dashboard/recommended.yaml")
                create_admin = os.system("kubectl apply -f /etc/kubernetes/dashboard/create-admin.yaml")
                dashboard_token = os.system("kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print $1}') -o go-template='{{.data.token}}' | base64 -d > /etc/kubernetes/admin-token.txt")
                print("*" * 20, "dashboard安装完成")
                print("*" * 20 ,"执行以下命令,检查K8s集群\n")
                print("*" * 20,"kubectl get nodes")
                print("*" * 20, "kubectl get cs")
                print("*" * 20, "kubectl get pod -n kube-system")
                print("-"* 20,"等待calico 相关服务为Running 即可登录控制台","-"* 20,"\n")
                print("请使用Firefox浏览器访问 https://%s:30001/#/login" % masterip_list[0])
                print("请使用/etc/kubernetes/admin-token.txt 中的密钥进行认证")
                print("提醒：kubernetes 的证书默认是一年，请及时修改\n")

            else:   #否则就是集群模式
                print("进入集群模式安装")
                print("暂无")
                exit()
            if masterip_list[0] == masterip:
                node_num = 0
                for nodeip in nodeip_list:  #安装从节点
                    print("*" * 20, "进入Node节点操作，当前IP: %s" % nodeip)
                    token_creat = token_creat[1].split('\n')[-1]
                    token_code = token_code[1]
                    node_num += 1
                    node_name = "node0%s" % (node_num)
                    # 设置名字
                    os.system("ssh %s \"hostname %s\"" % (nodeip,node_name))
                    os.system("ssh %s \"echo '%s' > /etc/hostname\"" % (nodeip,node_name))
                    print("*" * 20, "进入环境初始化，请耐心等待....")
                    for shell in self.initialization_shell():
                        os.system("ssh %s \"%s\"" %(nodeip,shell))
                    print("*" * 20, "正在加入集群....")
                    kubeadm_join = os.system("ssh %s \"kubeadm join %s:6443 --token %s --discovery-token-ca-cert-hash sha256:%s\"" % (nodeip,masterip, str(token_creat), str(token_code)))
                    print("*" * 20, "加入集群成功....")

if __name__ == '__main__':
    # #用户输入IP:
    print("----------0、请先安装python3 并使用python3 执行此脚本------------")
    print("----------1、此脚本依赖网络，请连接好网络执行此脚本-----------")
    print("----------2、请将此脚本在主节点上执行，请在主节点上对其他所有节点做免密登录-----------")
    print("**********3、请确认主节点已对其他节点做好免密登录，再次确认后再执行此脚本**********")
    k8s_masterip = input("请输入K8S_Master IP, 多个IP以逗号分隔: ")
    k8s_nodeip = input("请输入K8S_node IP,多个IP以逗号分隔: ")
    ask_ent = input("**********   确认/取消 (Y/N) :")
    if ask_ent.upper() == "Y":
        k8s_install = k8s_install(k8s_masterip,k8s_nodeip)
        k8s_install.shell_command()
    else:
        exit()