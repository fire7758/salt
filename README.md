
## 2016/1/26 ##
一、 扩展模块
	1.功能说明及使用方法
		添加文件md5校验
		salt '*' check.file salt://path/to/file /minion/dest

		添加master文件推送和拉去，带回文件列表及MD5
		salt '*' cp_fire.get_file salt://path/to/file /minion/dest
		salt '*' cp_fire.get_dir salt://path/to/dir /minion/dest
		salt '*' cp_fire.push /etc/fstab		salt '*' cp_fire.push /etc/system-release keep_symlinks=True
		salt '*' cp_fire.push_dir /tmp/config		salt '*' cp_fire.push_dir /etc/modprobe.d/ glob='*.conf'

	2.部署扩展模块
		将_modules文件夹部署到/srv/salt，并执行salt \* saltutil.sync_modules

二、 修改源码
	1.修改salt.client模块，加入client:local执行结果带回jid（修改549行中的return）
	2.重启salt-api
