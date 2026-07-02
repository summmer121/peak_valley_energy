# 峰谷电价 (Peak Valley Energy)

Home Assistant 自定义集成，用于监控总电量传感器并自动拆分为峰、谷、平时段用电量及电费统计。

## ✨ 功能特性

- 📊 **实时监控**：监听任意总电量传感器（kWh 累计值），自动判断当前时段
- ⚡ **峰谷拆分**：支持双峰段（如 8:00-11:00, 18:00-21:00）+ 可选平段
- 💰 **电费计算**：峰/谷/平单价可自定义，支持任意精度（如 0.5583 元/kWh）
- 💲 **实时电价**：根据当前时段自动显示实时电单价（¥/kWh）
- 📅 **多维度统计**：自动生成本日/本月/本年的电量和电费数据
- 💾 **数据持久化**：每 5 分钟自动保存，重启不丢失
- 🔄 **自动滚动**：每天午夜自动重置日统计，月初/年初自动重置月/年统计
- 🛡️ **容错机制**：电表重置或数据异常时自动重新基线

## 📦 安装

### 方法一：HACS 自定义仓库（推荐）

1. 在 HACS 中点击 **集成 → 右上角菜单 → 自定义存储库**
2. 填入仓库地址：`https://github.com/summmer121/peak_valley_energy`
3. 类别选择 **集成 (Integration)**
4. 点击添加，然后在 HACS 中搜索 "Peak Valley Energy" 安装
5. 重启 Home Assistant

### 方法二：手动安装

将整个仓库克隆或下载后，把 `custom_components/peak_valley_energy/` 文件夹复制到你的 HA 配置目录：

```
/config/custom_components/peak_valley_energy/
```

然后重启 Home Assistant。

## 🚀 使用方法

### 1. 添加集成
- 进入 **设置 → 设备与服务 → 添加集成**
- 搜索 **"Peak Valley Energy"** 或 **"峰谷电价"**
- 点击添加

### 2. 配置参数

#### 第一步：基础配置
| 参数 | 说明 | 示例 |
|------|------|------|
| **集成名称** | 自定义名称 | `家庭峰谷电价` |
| **总电量传感器** | 选择你的总电量实体 | `sensor.total_energy` |
| **第一峰段开始** | 上午峰段开始时间 | `08:00:00` |
| **第一峰段结束** | 上午峰段结束时间 | `11:00:00` |
| **第二峰段开始** | 晚上峰段开始时间（可选） | `18:00:00` |
| **第二峰段结束** | 晚上峰段结束时间（可选） | `21:00:00` |
| **峰段电价** | 元/kWh | `0.5583` |
| **谷段电价** | 元/kWh | `0.3583` |
| **启用平段** | 是否启用尖峰平谷三段制 | `否` |

#### 第二步：平段配置（可选）
如果启用了平段，继续配置：
| 参数 | 说明 | 示例 |
|------|------|------|
| **平段开始时间** | 平段开始 | `06:00:00` |
| **平段结束时间** | 平段结束 | `08:00:00` |
| **平段电价** | 元/kWh | `0.4583` |
| **货币单位** | 货币符号 | `CNY` |

### 3. 生成的传感器实体

配置完成后，集成会自动创建 **25 个传感器实体**：

#### 📅 日统计（8 个）
- `sensor.{name}_daily_peak_kwh` - 本日峰电量
- `sensor.{name}_daily_valley_kwh` - 本日谷电量
- `sensor.{name}_daily_shoulder_kwh` - 本日平电量
- `sensor.{name}_daily_total_kwh` - 本日总电量
- `sensor.{name}_daily_peak_cost` - 本日峰电费
- `sensor.{name}_daily_valley_cost` - 本日谷电费
- `sensor.{name}_daily_shoulder_cost` - 本日平电费
- `sensor.{name}_daily_total_cost` - 本日总电费

#### 📆 月统计（8 个）
- `sensor.{name}_monthly_peak_kwh` - 本月峰电量
- `sensor.{name}_monthly_valley_kwh` - 本月谷电量
- `sensor.{name}_monthly_shoulder_kwh` - 本月平电量
- `sensor.{name}_monthly_total_kwh` - 本月总电量
- `sensor.{name}_monthly_peak_cost` - 本月峰电费
- `sensor.{name}_monthly_valley_cost` - 本月谷电费
- `sensor.{name}_monthly_shoulder_cost` - 本月平电费
- `sensor.{name}_monthly_total_cost` - 本月总电费

#### 📊 年统计（8 个）
- `sensor.{name}_yearly_peak_kwh` - 本年峰电量
- `sensor.{name}_yearly_valley_kwh` - 本年谷电量
- `sensor.{name}_yearly_shoulder_kwh` - 本年平电量
- `sensor.{name}_yearly_total_kwh` - 本年总电量
- `sensor.{name}_yearly_peak_cost` - 本年峰电费
- `sensor.{name}_yearly_valley_cost` - 本年谷电费
- `sensor.{name}_yearly_shoulder_cost` - 本年平电费
- `sensor.{name}_yearly_total_cost` - 本年总电费

#### 💲 实时电价（1 个）
- `sensor.{name}_current_price` - 当前电价（¥/kWh），根据当前时段自动变化

## ⚙️ 工作原理

### 核心逻辑
1. **监听电量变化**：集成监听你选择的总电量传感器
2. **计算增量**：当电量增加时，计算 `delta = 新值 - 旧值`
3. **判断时段**：根据当前时间判断属于峰/谷/平哪个时段
4. **累加统计**：将 delta 累加到对应时段的日/月/年计数器
5. **计算费用**：`费用 = delta × 单价`
6. **实时电价**：根据当前时段返回对应单价

### 时段判断规则
- 如果当前时间在**峰段 1** 或**峰段 2** → 归为峰电量
- 如果启用平段，且当前时间在**平段** → 归为平电量
- 其他时间 → 归为谷电量

### 滚动重置机制
- **每天 00:00:01**：重置日统计（自动保存前一天数据）
- **每月 1 日**：重置月统计
- **每年 1 月 1 日**：重置年统计

## 💡 使用场景

### 1. 能耗仪表板
在 Lovelace 仪表板中添加卡片：
```yaml
type: entities
title: 今日用电
entities:
  - entity: sensor.峰谷电价_daily_peak_kwh
    name: 峰电量
  - entity: sensor.峰谷电价_daily_valley_kwh
    name: 谷电量
  - entity: sensor.峰谷电价_daily_total_kwh
    name: 总电量
  - entity: sensor.峰谷电价_daily_total_cost
    name: 总电费
  - entity: sensor.峰谷电价_current_price
    name: 当前电价
```

### 2. 自动化通知
每天晚上 10 点推送今日用电：
```yaml
automation:
  - alias: "每日电费通知"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      service: notify.mobile_app
      data:
        title: "今日用电统计"
        message: >
          峰电: {{ states('sensor.峰谷电价_daily_peak_kwh') }} kWh ({{ states('sensor.峰谷电价_daily_peak_cost') }} 元)
          谷电: {{ states('sensor.峰谷电价_daily_valley_kwh') }} kWh ({{ states('sensor.峰谷电价_daily_valley_cost') }} 元)
          总计: {{ states('sensor.峰谷电价_daily_total_cost') }} 元
```

### 3. 成本优化建议
根据峰谷比例优化用电习惯：
```yaml
sensor:
  - platform: template
    sensors:
      peak_ratio:
        friendly_name: "峰电占比"
        unit_of_measurement: "%"
        value_template: >
          {% set peak = states('sensor.峰谷电价_monthly_peak_kwh') | float %}
          {% set total = states('sensor.峰谷电价_monthly_total_kwh') | float %}
          {{ ((peak / total * 100) | round(1)) if total > 0 else 0 }}
```

## 🔧 高级配置

### 修改峰谷时段和电价
配置完成后，可在 **设备与服务** 中点击集成的 **配置** 按钮修改：
- 峰谷时段
- 电价单价

## 🐛 故障排查

### 问题 1：传感器没有更新
**原因**：总电量传感器未正常更新  
**解决**：检查源传感器是否正常工作，确认 `device_class: energy` 已设置

### 问题 2：电费计算不准确
**原因**：电价配置错误或时段设置有误  
**解决**：
1. 检查峰谷时段是否覆盖全天（谷段自动填补空隙）
2. 确认电价单位为 **元/kWh**（不是 **分/kWh**）

### 问题 3：数据在重启后丢失
**原因**：存储文件损坏  
**解决**：检查 `/config/.storage/peak_valley_energy_data_{entry_id}` 文件权限

### 问题 4：集成无法加载
**原因**：Home Assistant 版本不兼容  
**解决**：确保 HA 版本 >= 2024.1.0

## 📝 常见问题

**Q：支持多个电表吗？**  
A：支持！每个电表添加一个集成实例即可。

**Q：可以设置三个峰段吗？**  
A：当前版本仅支持双峰段，未来版本会扩展支持。

**Q：电表重置后会怎样？**  
A：集成会自动检测到电量下降，重新基线，不影响历史统计。

**Q：如何查看历史数据？**  
A：所有传感器都支持 Home Assistant 历史记录，可在**历史**页面查看趋势图。

**Q：平段必须设置吗？**  
A：不是必须的。如果你的电价只有峰谷两段，关闭"启用平段"即可。

## 🛠️ 技术细节

### 文件结构
```
peak_valley_energy/
├── custom_components/
│   └── peak_valley_energy/
│       ├── __init__.py           # 核心逻辑：监听、计算、存储
│       ├── config_flow.py        # 配置流程
│       ├── const.py              # 常量定义
│       ├── sensor.py             # 传感器实体定义
│       ├── manifest.json         # 集成元数据
│       ├── strings.json          # 中文翻译
│       ├── services.yaml         # 服务定义
│       ├── translations/
│       │   ├── en.json          # 英文翻译
│       │   └── zh-Hans.json     # 简体中文翻译
│       └── brand/               # 图标资源
└── README.md                    # 本文档
```

### 数据存储
数据保存在 Home Assistant 的 `.storage` 目录：
```
/config/.storage/peak_valley_energy_data_{entry_id}
```

存储格式（JSON）：
```json
{
  "daily": {"peak": 3.2, "valley": 1.5, "shoulder": 0.3, "total": 5.0},
  "daily_cost": {"peak": 2.18, "valley": 0.47, "shoulder": 0.15, "total": 2.79},
  "monthly": {...},
  "yearly": {...},
  "last_energy": 12345.678,
  "last_update": "2025-06-15T19:30:00"
}
```

### 性能优化
- 采用 listener 模式，不轮询，零性能损耗
- 增量计算，仅在电量变化时触发
- 每 5 分钟批量保存，减少磁盘 I/O

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**作者**：summer  
**版本**：1.1.0  
**最后更新**：2025-07-02
