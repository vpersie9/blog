Web博客的设计和部署：
MVC架构下使用Python + flask框架搭建web应用；并通过注册蓝本实现程序的模块化；
并使用Flask扩展优化工程。

视图认证和信息资料模块：
Flask-Login扩展：管理用户登录会话
Werkzeug：计算密码散列值并进行密码核对
Isdangerous：生成并核对加密安全令牌
Flask-mail：发送认证电子邮件
Flask-Bootstrap：集成HTML模板
Flask-WTF：web表单
Flask-PageDown、MarkDown：集成富文本编辑器实现用户文章发布
Flask-Moment：用户登录时间更新
数据模型模块：
Flask-SQLAlchemy：使用ORM（对象关系映射）操作数据库
控制模块：
Flask-Script：连接终端shell
Flask-Migrate：实现数据库迁移
实现与数据库交互，通过Mysql数据库处理用户数据和信息；实现用户注册、登录、注销、文章发布、评论、用户关注等功能；使用virtualenv搭建Python的虚拟运行环境、并进行依赖安装。通过Nginx的配置实现Nginx服务器的反向代理，最后使用supervisor通过新建配置文件配置Gunicorn的启动端口，实现supervisor管理web博客进程，实现部署。
