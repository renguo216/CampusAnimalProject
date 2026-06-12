# CampusAnimalProject

校园流浪动物智慧互助平台

## 项目简介

本项目是一个基于微信小程序的校园流浪动物智慧互助平台。

## 技术栈
- 后端框架 : Flask (Python)
- 前端 : 微信小程序 + 管理员后台（HTML/CSS/JavaScript）
- 数据库 : MySQL
- AI模块 : TensorFlow + ResNet50（动物识别）

## 项目结构
CampusAnimalProject/
├── backend/          # 后端代码
│   ├── app.py        # Flask应用入口
│   ├── api/          # RESTful API路由
│   ├── libs/         # 业务逻辑层
│   ├── model/        # 数据模型
│   ├── utils/        # 工具类（数据库管理、响应封装）
│   ├── ai_module/    # AI动物识别模块
│   └── config/       # 配置文件
├── database/         # 数据库脚本（建表、初始化数据）
├── admin/            # 管理员后台页面
├── frontend/         # 微信小程序前端
└── docs/             # 项目文档

## 核心功能
### 用户端功能
- 动物档案管理 : 查看校园流浪动物信息、照片、健康状态
- 一键救助 : 提交流浪动物救助申请
- 领养申请 : 申请领养校园动物
- 志愿者招募 : 申请成为志愿者
- 积分商城 : 积分兑换公益礼品
- 社区互动 : 发布动态、点赞评论
- 捐款功能 : 为流浪动物捐款

### 管理端功能
- 用户管理 : 用户列表、角色管理、封禁操作
- 动物管理 : 动物档案录入、状态更新
- 志愿者管理 : 申请审核、等级管理
- 领养管理 : 领养申请审核
- 救助管理 : 救助记录管理
- 捐款管理 : 捐款审核、项目管理
- 数据统计 : 仪表盘数据展示

### AI功能
- 猫狗检测 : 自动识别图片中的猫/狗
- 品种识别 : 识别动物品种

## 数据库表结构（核心数据表）
- t_user - 用户信息表
- t_animal - 动物档案表
- t_rescue_record - 救助记录表
- t_adoption_apply - 领养申请表
- t_volunteer_application - 志愿者申请表
- t_donation - 捐款记录表
- t_post - 社区动态表

## 快速开始
### 环境要求
- Python 3.8+
- MySQL 5.7+
- Node.js（小程序开发）

### 后端启动
cd backend
pip install -r requirements.txt
set PYTHONPATH=your_project_path
python app.py

### 访问地址
- API接口 : http://localhost:5000/api/v1
- 管理后台 : http://localhost:5000/admin/index.html
