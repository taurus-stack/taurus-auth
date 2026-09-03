# 贡献指南

感谢您对 Taurus Auth 项目的兴趣！本文档提供了贡献的指南和说明。

## 行为准则

参与本项目即表示您同意遵守我们的[行为准则](CODE_OF_CONDUCT.zh-CN.md)。

## 如何贡献

### 报告 Bug

在创建 Bug 报告之前，请先检查问题列表，因为您可能不需要创建新的问题。创建 Bug 报告时，请包含尽可能多的详细信息：

* 使用清晰描述性的标题
* 描述重现问题的具体步骤
* 提供具体的示例来演示这些步骤
* 描述您观察到的行为
* 解释您期望看到的行为以及原因
* 如果可能，包含日志和堆栈跟踪

### 建议增强功能

增强建议作为 GitHub 问题进行跟踪。创建增强建议时，请包含：

* 使用清晰描述性的标题
* 提供建议增强的逐步描述
* 提供具体的示例来演示这些步骤
* 描述当前行为并解释您期望看到的行为
* 解释为什么这个增强会很有用

### Pull Requests

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 进行更改
4. 运行测试 (`poetry run pytest`)
5. 提交更改 (`git commit -m 'Add amazing feature'`)
6. 推送到分支 (`git push origin feature/amazing-feature`)
7. 开启 Pull Request

## 开发环境设置

### 前置要求

- Python 3.10+
- Poetry
- MySQL/MariaDB
- Redis

### 设置步骤

```bash
# 克隆您的 fork
git clone https://github.com/YOUR_USERNAME/taurus-auth.git
cd taurus-auth

# 安装依赖
poetry install

# 复制环境文件
cp .env.example .env

# 编辑 .env 文件配置您的设置

# 运行数据库迁移
poetry run python manage.py migrate

# 运行测试
poetry run pytest
```

### 代码风格

我们使用以下工具来维护代码质量：

- **Black** 用于代码格式化
- **isort** 用于导入排序
- **flake8** 用于代码检查
- **mypy** 用于类型检查

```bash
# 格式化代码
poetry run black .
poetry run isort .

# 运行代码检查
poetry run flake8
poetry run mypy ticket/
```

### 测试

```bash
# 运行所有测试
poetry run pytest

# 运行覆盖率测试
poetry run pytest --cov=ticket

# 运行特定测试
poetry run pytest test_jwt_auth.py
```

## 项目结构

```
taurus-auth/
├── taurus_auth/          # Django 项目配置
│   ├── settings.py       # 项目设置
│   ├── urls.py           # 主路由
│   ├── wsgi.py           # WSGI 配置
│   └── asgi.py           # ASGI 配置
├── ticket/               # 票据认证应用
│   ├── models.py         # 数据模型
│   ├── views.py          # API 视图
│   ├── serializers.py    # 序列化器
│   ├── services.py       # 业务逻辑
│   ├── middleware.py     # 安全中间件
│   ├── urls.py           # 应用路由
│   └── utils/            # 工具类
│       └── jwt_helper.py # JWT 工具
├── manage.py             # Django 管理脚本
├── pyproject.toml        # Poetry 配置
└── test_jwt_auth.py      # JWT 测试
```

## 提交消息

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <description>

[可选的正文]

[可选的页脚]
```

类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更改
- `style`: 代码风格更改
- `refactor`: 代码重构
- `test`: 测试更改
- `chore`: 构建过程或辅助工具更改

示例：
```
feat(ticket): 添加自定义票据元数据支持
```

## 许可证

通过贡献，您同意您的贡献将根据 GNU Affero General Public License v3.0 进行许可。
