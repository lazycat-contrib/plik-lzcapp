# Plik 懒猫微服包

自托管文件分享：上传得到链接，支持有效期、一次性下载与密码保护。

- 上游：<https://github.com/root-gg/plik>
- 镜像：`rootgg/plik`
- 许可：MIT（全文见 content/licenses/LICENSE；已核对无子目录覆盖条款）

## 组成

单容器，监听 8080 端口；文件存储与 SQLite 数据库都在同一个持久化目录里。

## 关键配置说明

- **用环境变量覆盖配置，不需要改配置文件**：镜像支持
  `PLIKD_DATA_BACKEND_CONFIG` / `PLIKD_METADATA_BACKEND_CONFIG`（JSON 形式），
  本包用它们把「文件目录」与「SQLite 路径」都指到持久化卷。
- **默认保持上游的 file + SQLite 组合**（官方 helm chart 的默认值即是如此），
  因此不需要额外的数据库或对象存储服务。
- **`PLIKD_ASSUME_HTTPS=false`**：TLS 由懒猫入口负责，
  容器内不启用 HSTS/secure cookie，避免反代下出问题。
- **`PLIKD_SOURCE_IP_HEADER=X-Forwarded-For`**：反代后取真实来源地址。
- **默认不开启登录**（上游 `FeatureAuthentication` 默认为 disabled），
  因此不加 `public_path`，访问由懒猫入口鉴权。

## 未验证部分

未在真机上实测：上传文件、生成与访问分享链接、一次性下载、密码保护、重启后数据留存。
