# -*- coding: utf-8 -*-

from acore_db_ssh_tunnel import ssh_tunnel


def create_ssh_tunnel():
    ssh_tunnel.create_ssh_tunnel(
        path_pem_file=path_pem_file,
        db_host=db_host,
        db_port=db_port,
        jump_host_username=jump_host_username,
        jump_host_public_ip=jump_host_public_ip,
    )


def list_ssh_tunnel():
    ssh_tunnel.list_ssh_tunnel(path_pem_file)


def test_ssh_tunnel():
    ssh_tunnel.test_ssh_tunnel(
        db_port=db_port,
        db_username=db_username,
        db_password=db_password,
        db_name=db_name,
    )


def kill_ssh_tunnel():
    ssh_tunnel.kill_ssh_tunnel(path_pem_file)


db_host = "my-server.1a2b3c4d5e6f.us-east-1.rds.amazonaws.com"
db_port = 3306
db_username = "admin"
db_password = "admin"
db_name = "my_database"
jump_host_username = "ubuntu"
jump_host_public_ip = "111.111.111.111"
path_pem_file = "/Users/myusername/ec2-key.pem"


create_ssh_tunnel()
list_ssh_tunnel()
test_ssh_tunnel()
kill_ssh_tunnel()
