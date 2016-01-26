
## 2016/1/26 ##
1. 模块添加
	添加check.py，  salt 192.168.103.134 check.file salt://config/init.sls /tmp/init.sls

	添加cp_fire.py, salt 192.168.103.134 cp_fire.get_file salt://config/init.sls /tmp/init.sls
			salt 192.168.103.134 cp_fire.get_dir salt://config /tmp

			salt 192.168.103.134 cp_mb.push /tmp/config/init.sls
			salt 192.168.103.134 cp_mb.push_dir /tmp/config
2. 修改源码
	修改salt.client模块，加入client:local执行结果带回jid
	修改549行中的return
