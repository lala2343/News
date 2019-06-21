from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from info import create_app, db, models

# 通过指定的配置名字创建对应的app
from info.models import User

app = create_app("development")
manager = Manager(app)
# 关联app 和 db
Migrate(app, db)
# 将迁移命令添加至manager中
manager.add_command("db", MigrateCommand)


@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def createsuperuser(name, password):
    if not all([name, password]):
        print("参数不足")
    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        return

    print("添加成功")


if __name__ == '__main__':
    manager.run()
