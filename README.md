## 一. 说明
脚本基于 python3 .

```
.
├── Pipfile
├── Pipfile.lock
├── README.md
├── etc
│   └── tools.cfg
└── src
    ├── config_parser.py
    └── jenkins_tools.py
```

安装依赖

```
$ pip install requests lxml python-jenkins click
```

## 二. 使用方法
### 配置 用户名和密码

**配置 tools.cfg 与 脚本文件, 在路径上存在依赖关系, 所以, 尽量不要 移动 文件位置.**

**[推荐]**也可以修改 `tools.cfg` 中的如下配置, **不要加引号**.
**tools.cfg 需要跟 脚本 位于相同的目录, 否则会找不到.**
```
$ vim etc/tools.cfg

  [jenkins]
  jenkins_url = http://example.jenkins.com
  admin_name = JENKINS_USER_NAME
  admin_pass = JENKINS_USER_PASS

```


可以直接在执行时, 传入用户名密码, 如下
```
$ ./jenkins_tools.py -U YOUR_NAME -P YOUR_PASS [...]
```

### jenkins_tools.py 示例
#### 0. 获取帮助信息
```
$ ./jenkins_tools.py --help

    Usage: jenkins_tools.py [OPTIONS] COMMAND [ARGS]...

    Options:
      -U, --admin-name TEXT  You Useranme to Login Jenkins Server.
      -P, --admin-pass TEXT  You Password to Login Jenkins Server.
      --help                 Show this message and exit.

    Commands:
      add-role
      assign-role
      delete-user
      remove-role
      unassign-role
```

获取子命令帮助:
```
$ ./jenkins_tools.py COMMAND --help
```
#### 1. 添加 role
`--role-pattern` 一般配置为 Jenkins 上项目的 CI 名称.

- 可以写正则, 如 `test-project.*`
- 多个规则一以 `|` 分割, 如 `test-project-a|test-project-b`
- 如果 role 已存在, 则 新的 role-pattern 会在以前的基础上添加.

```
$ ./jenkins_tools.py add-role --role-name="test" --role-pattern='test_project*'
```
#### 2. 删除 role
```
$ ./jenkins_tools.py remove-role --role-name="devops-test"
```

#### 3. 分配 role

```
$ ./jenkins_tools.py assign-role --role-name="devops-test" --user-name="tom"
```

#### 4. 取消分配 role

```
$ ./jenkins_tools.py unassign-role --role-name="devops-test" --user-name="tom"
```
