import os
import configparser

etc_name = "etc"
config_name = "tools.cfg"

def get_etc_dir():
	current_dir = os.path.abspath(".")

	if os.path.isdir(os.path.join(os.path.dirname(current_dir), etc_name)):
		return os.path.join(os.path.dirname(current_dir), etc_name)
	elif os.path.isdir(os.path.join(current_dir, etc_name)):
		return os.path.join(current_dir, etc_name)
	else:
		raise ValueError("当前工作目录错误: %s. 必须位于 命令行工具 相同目录或上层目录." % current_dir)


def get_section(sec):
	etc_dir = get_etc_dir()
	CONFIG_FILE = os.path.join(etc_dir, config_name)
	
	if os.path.isfile(CONFIG_FILE):
		cf = configparser.ConfigParser()
		cf.read(CONFIG_FILE)
		return dict(cf.items(sec))
	
	raise ValueError("File %s not exist!" % CONFIG_FILE)

