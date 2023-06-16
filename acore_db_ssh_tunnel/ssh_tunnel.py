# -*- coding: utf-8 -*-

"""
SSH Tunnel management automation tool.

You have to have an ec2 key pair (.pem) file for your jump host.

https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html

Reference:

- SSH Tunneling: Examples, Command, Server Config: https://www.ssh.com/academy/ssh/tunneling-example

**创建 SSH Tunnel 的自动化脚本**

由于游戏数据库通常是位于 Private Subnet 中的. 而 Python 脚本又通常在本地电脑上运行.
为了让本地电脑和游戏数据库通信, 需要利用 EC2 做 SSH Tunnel 的桥梁. 具体方法是用 SSH 和
EC2 的秘钥在本地机器上建立一个 tunnel, 所有本来要发送到 Database domain 的流量都发送到
127.0.0.1, 然后 SSH 会自动将流量转发至 Database.

.. note::

    本模块不考虑用一个 pem 秘钥开启多个 SSH Tunnel 连接到不同跳板机的情况. 我们假设同一时间
    一个秘钥只能创建一个 SSH Tunnel.


"""

import typing as T
import subprocess
from pathlib import Path

import sqlalchemy as sa
from .mysql_engine import create_engine


def create_ssh_tunnel(
    path_pem_file,
    db_host: str,
    db_port: int,
    jump_host_username: str,
    jump_host_public_ip: str,
    verbose: bool = True,
    print_func: T.Callable = print,
):
    """
    创建一个 SSH Tunnel 连接到游戏数据库. 建议完成后使用 :func:`test_ssh_tunnel` 函数进行测试.

    :param path_pem_file: AWS SSH pem 秘钥的路径.
    :param db_host: 数据库的 endpoint, 在此情况下一般是私网的 IP. 如果是 AWS RDS, 则是 RDS 的 endpoint.
    :param db_port: 数据库的端口. 在本项目中数据库是 MySQL, 所以端口通常是 3306.
    :param jump_host_username: 跳板机的操作系统用户名, 用与创建 SSH 连接.
    :param jump_host_public_ip: 跳板机的公网 IP 地址.
    :param verbose: 是否打印详细的 SSH Tunnel 命令.
    :param print_func: 打印函数. 默认是 print, 你可以用自定义的 logger 来替换它.
    """
    path_pem_file = Path(path_pem_file).absolute()
    if path_pem_file.exists() is False:
        raise FileNotFoundError(f"pem file not found at {path_pem_file}.")
    args = [
        "ssh",
        "-i",
        f"{pem_file}",
        "-f",
        "-N",
        "-L",
        f"{db_port}:{db_host}:{db_port}",
        f"{jump_host_username}@{jump_host_public_ip}",
        "-v",
    ]
    if verbose:
        ssh_cmd = " ".join(args)
        print_func(f"Open ssh tunnel by running the following command:")
        print_func("")
        print_func(f"  {ssh_cmd}")
    subprocess.run(args)
    return args


def list_ssh_tunnel_pid(path_pem_file) -> T.List[str]:
    """
    找出在本地机器上已有的 SSH Tunnel 的 PID (process id, 即进程 ID). 其原理是用
    `ps aux <https://www.linode.com/docs/guides/use-the-ps-aux-command-in-linux/>`_
    命令以 BSD 的格式列出所有进程, 而这个进程一定是包含 ``ssh`` 的. 然后再用 python 捕获
    这些进程列表, 这些进程里包含 pem 文件路径的就一定是我们要找的 SSH Tunnel 进程.

    :param path_pem_file: AWS SSH pem 秘钥的路径.

    :return: SSH Tunnel 进程的 PID 列表.
    """
    path_pem_file = str(Path(path_pem_file).absolute())
    pipe = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    res = subprocess.run(["grep", "ssh"], stdin=pipe.stdout, capture_output=True)
    pid_list = []
    for line in res.stdout.decode("utf-8").strip().split("\n"):
        if path_pem_file in line:
            words = [word.strip() for word in line.split(" ") if word.strip()]
            pid = words[1]
            pid_list.append(pid)
    return pid_list


def list_ssh_tunnel(
    path_pem_file: str,
    print_func: T.Callable = print,
):
    """
    列出在本地机器上用特定 pem 秘钥创建的 SSH Tunnel. 其原理请参考 :func:`list_ssh_tunnel_pid`.

    :param path_pem_file: AWS SSH pem 秘钥的路径.
    :param print_func: 打印函数. 默认是 print, 你可以用自定义的 logger 来替换它.
    """
    path_pem_file = str(Path(path_pem_file).absolute())
    pipe = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    res = subprocess.run(["grep", "ssh"], stdin=pipe.stdout, capture_output=True)
    lines = list()
    for line in res.stdout.decode("utf-8").strip().split("\n"):
        if path_pem_file in line:
            lines.append(line)

    if len(lines):
        print_func("List SSH tunnel ...")
        print_func("")
        for line in lines:
            print_func(line)
    else:
        print_func("There's NO existing SSH tunnel.")


def kill_ssh_tunnel(
    path_pem_file: str,
    verbose: bool = True,
    print_func: T.Callable = print,
):
    """
    关闭所有在本地机器上用特定 pem 秘钥创建的 SSH Tunnel. 其原理是用
    :func:`list_ssh_tunnel_pid` 函数找到这些 SSH Tunnel 的进程 ID 然后将其杀死.

    Reference:

    - How to close this ssh tunnel? https://stackoverflow.com/questions/9447226/how-to-close-this-ssh-tunnel

    :param path_pem_file: AWS SSH pem 秘钥的路径.
    :param verbose: 是否打印详细的 SSH Tunnel 命令.
    :param print_func: 打印函数. 默认是 print, 你可以用自定义的 logger 来替换它.

    :return: SSH Tunnel 进程的 PID 列表.
    """
    pid_list = list_ssh_tunnel_pid(path_pem_file)
    if len(pid_list):
        for pid in pid_list:
            if verbose:
                print_func(f"Found pid {pid}, try to kill it")
            subprocess.run(["kill", pid])
    else:
        if verbose:
            print_func("There's NO existing SSH tunnel to kill.")


def test_ssh_tunnel(
    db_port: int,
    db_username: str,
    db_password: str,
    db_name: str,
    timeout: int = 5,
    sql: str = "SELECT * FROM acore_auth.realmlist LIMIT 1;",  # you can also use "SELECT 1;"
    verbose: bool = True,
    print_func: T.Callable = print,
) -> bool:
    """
    测试 SSH Tunnel 是否正常工作. 其原理是用 SQLAlchemy 创建一个数据库连接, 然后执行一个简单
    SQL 命令.

    :param db_port: 数据库的端口. 在本项目中数据库是 MySQL, 所以端口通常是 3306.
        之所以不需要 db_host 的原因是我们使用了 SSH tunnel, 所以 db_host 是 127.0.0.1.
    :param db_username: 数据库用户名.
    :param db_password: 数据库密码.
    :param db_name: 数据库名.
    :param timeout: 测试的连接超时秒.
    :param sql: 测试用的 SQL 命令. 默认是 ``SELECT * FROM acore_auth.realmlist LIMIT 1;``.
    :param verbose: 是否打印详细的 SSH Tunnel 命令.
    :param print_func: 打印函数. 默认是 print, 你可以用自定义的 logger 来替换它.

    :return: 如果 SSH Tunnel 正常工作, 返回 True, 否则返回 False.
    """
    if verbose:
        print_func(
            "Test SSH Tunnel Connection, if you see a "
            "dictionary record means that it works:"
        )
        print_func("")
    engine = create_engine(
        host="127.0.0.1",
        port=db_port,
        username=db_username,
        password=db_password,
        db_name=db_name,
        connect_args={"timeout": timeout},
    )
    try:
        with engine.connect() as connect:
            sql_stmt = sa.text(sql)
            if verbose:
                print_func(str(dict(connect.execute(sql_stmt).one())))
        return True
    except TimeoutError:
        return False


# Sample usage:
if __name__ == "__main__":
    db_host = "my-server.1a2b3c4d5e6f.us-east-1.rds.amazonaws.com"
    db_port = 3306
    db_username = "admin"
    db_password = "admin"
    db_database = "my_database"
    jump_host_username = "ubuntu"
    jump_host_public_ip = "111.111.111.111"
    pem_file = "/Users/myusername/ec2-key.pem"

    create_ssh_tunnel(
        pem_file, db_host, db_port, jump_host_username, jump_host_public_ip
    )
    # test_ssh_tunnel(db_port, db_username, db_password, db_database)
    # list_ssh_tunnel(pem_file)
    # kill_ssh_tunnel(pem_file)
    pass
