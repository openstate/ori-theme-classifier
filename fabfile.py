from fabric.api import run, env, cd, sudo

env.use_ssh_config = True
env.hosts = ["Oxygen"]


def deploy():
    with cd('/home/projects/ori-theme-classifier'):
        run('git pull git@github.com:openstate/ori-theme-classifier.git')
        run('touch uwsgi-touch-reload')
        #sudo('docker exec otc_nginx_1 nginx -s reload')
