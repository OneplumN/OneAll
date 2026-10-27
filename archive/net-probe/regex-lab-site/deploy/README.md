# regex.oneplums.cn 部署

- 网站文件：服务器 `/var/www/regex.oneplums.cn/`，来自本项目的 `dist/`。
- Web 服务：Ubuntu 22.04 的 Nginx；站点配置位于 `/etc/nginx/sites-available/regex.oneplums.cn`，通过 `sites-enabled` 启用。
- 当前 DNS：阿里云 CNAME `regex.oneplums.cn` 指向 `custom-domains.chatgpt.site.`，网页由 Sites 托管。
- HTTPS：Certbot 签发的 Let's Encrypt 证书，证书名 `regex.oneplums.cn`。`snap.certbot.renew.timer` 自动续期；已通过 `certbot renew --dry-run`。
- 上海 ECS 已准备好网站文件和 Nginx 配置，但公网访问被服务商的 ICP 备案检查拦截，目前不承载此域名。完成备案或接入备案并验证可访问后，才能考虑将 DNS 切回服务器。
- 当前更新网页时，通过 Sites 项目的发布流程发布 `dist/`。若以后切回服务器，再把 `dist/` 的文件复制到服务器网站目录；修改 Nginx 配置后运行 `nginx -t` 和 `systemctl reload nginx`。

原 IP 正则算法保存在 `src/ipRegexTool.ts`，与原项目文件一致。不要在部署过程中修改该逻辑。
