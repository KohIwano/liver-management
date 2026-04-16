#!/usr/bin/env python3
"""ライバー管理システム

使い方:
  python manage.py "名前" "やり取り内容"   # 記録を追加・更新してHTMLを生成
  python manage.py --report                # HTMLのみ再生成
"""

import json
import sys
import os
from datetime import datetime, date

DATA_FILE = os.path.join(os.path.dirname(__file__), "livers.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "report.html")


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # 最新のやり取り日付とlast_contactをリンク
    for liver in data:
        history = liver.get("history", [])
        if history:
            dates = [h["date"] for h in history]
            latest_date = max(dates)
            if liver.get("last_contact") != latest_date:
                liver["last_contact"] = latest_date

    return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_liver(name: str, content: str):
    data = load_data()
    today = date.today().isoformat()

    for liver in data:
        if liver["name"] == name:
            liver["last_contact"] = today
            liver["history"].append({"date": today, "content": content})
            print(f"更新: {name} ({today})")
            save_data(data)
            return

    # 新規追加
    data.append({
        "name": name,
        "last_contact": today,
        "history": [{"date": today, "content": content}]
    })
    print(f"新規登録: {name} ({today})")
    save_data(data)


def days_since(date_str: str) -> int:
    last = date.fromisoformat(date_str)
    return (date.today() - last).days


def generate_html():
    data = load_data()

    # データをファイルに保存（同期を反映）
    save_data(data)

    # 最近のやり取りの日付を参照して、古い順に並べる（連絡が空いている順）
    def get_latest_contact_date(liver):
        history = liver.get("history", [])
        if history:
            dates = [h["date"] for h in history]
            return max(dates)  # 最新の日付を取得
        return liver.get("last_contact", "1970-01-01")

    sorted_data = sorted(
        data,
        key=get_latest_contact_date
    )

    rows_html = ""
    for liver in sorted_data:
        name = liver["name"]
        last_contact = liver.get("last_contact", "未記録")
        history = liver.get("history", [])
        days = days_since(last_contact) if last_contact != "未記録" else 9999

        # バッジ
        if days >= 14:
            badge = '<span class="badge badge-danger">⚠ 2週間超</span>'
            row_class = "row-danger"
        elif days >= 7:
            badge = '<span class="badge badge-warning">! 1週間超</span>'
            row_class = "row-warning"
        else:
            badge = '<span class="badge badge-ok">✓ 連絡済</span>'
            row_class = ""

        # 最新やり取り（最新3件）
        recent = history[-3:] if history else []
        recent.reverse()
        history_html = ""
        for h in recent:
            history_html += f"""
            <div class="history-item">
              <span class="history-date">{h['date']}</span>
              <span class="history-content">{h['content']}</span>
            </div>"""

        rows_html += f"""
      <div class="card {row_class}">
        <div class="card-header">
          <div class="liver-info">
            <span class="liver-name">{name}</span>
            {badge}
          </div>
          <div class="last-contact">
            <span class="label">最終連絡日</span>
            <span class="date-value">{last_contact}</span>
            <span class="days-ago">({days}日前)</span>
          </div>
        </div>
        <div class="card-body">
          <p class="history-title">最近のやり取り</p>
          {history_html if history_html else '<p class="no-history">記録なし</p>'}
        </div>
      </div>"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(data)
    warning_count = sum(1 for x in data if days_since(x.get("last_contact", "1970-01-01")) >= 7)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ライバー管理レポート</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Hiragino Sans', sans-serif;
      background: #f0f2f5;
      color: #1a1a2e;
      min-height: 100vh;
    }}

    .header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      color: white;
      padding: 32px 24px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}

    .header h1 {{
      font-size: 28px;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }}

    .header .subtitle {{
      font-size: 13px;
      opacity: 0.6;
    }}

    .stats-bar {{
      background: white;
      padding: 16px 24px;
      display: flex;
      gap: 32px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      border-bottom: 1px solid #e8eaf0;
    }}

    .stat-item {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .stat-label {{
      font-size: 13px;
      color: #666;
    }}

    .stat-value {{
      font-size: 20px;
      font-weight: 700;
      color: #1a1a2e;
    }}

    .stat-value.warning {{
      color: #e67e22;
    }}

    .container {{
      max-width: 900px;
      margin: 32px auto;
      padding: 0 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}

    .card {{
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
      overflow: hidden;
      border-left: 4px solid #e8eaf0;
      transition: transform 0.15s, box-shadow 0.15s;
    }}

    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 6px 24px rgba(0,0,0,0.1);
    }}

    .row-warning {{
      border-left-color: #f39c12;
      background: linear-gradient(to right, #fffbf0, white 80px);
    }}

    .row-danger {{
      border-left-color: #e74c3c;
      background: linear-gradient(to right, #fff5f5, white 80px);
    }}

    .card-header {{
      padding: 18px 20px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #f0f2f5;
    }}

    .liver-info {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .liver-name {{
      font-size: 18px;
      font-weight: 700;
      color: #1a1a2e;
    }}

    .badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 20px;
      letter-spacing: 0.03em;
    }}

    .badge-ok {{
      background: #e8f8f0;
      color: #27ae60;
    }}

    .badge-warning {{
      background: #fef5e0;
      color: #e67e22;
    }}

    .badge-danger {{
      background: #fdecea;
      color: #c0392b;
    }}

    .last-contact {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
    }}

    .label {{
      color: #999;
      font-size: 12px;
    }}

    .date-value {{
      font-weight: 600;
      color: #333;
    }}

    .days-ago {{
      color: #aaa;
      font-size: 12px;
    }}

    .card-body {{
      padding: 14px 20px 16px;
    }}

    .history-title {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #aaa;
      margin-bottom: 10px;
    }}

    .history-item {{
      display: flex;
      gap: 12px;
      padding: 7px 0;
      border-bottom: 1px solid #f5f5f7;
      align-items: baseline;
    }}

    .history-item:last-child {{
      border-bottom: none;
    }}

    .history-date {{
      font-size: 12px;
      color: #999;
      white-space: nowrap;
      min-width: 90px;
    }}

    .history-content {{
      font-size: 14px;
      color: #444;
      line-height: 1.5;
    }}

    .no-history {{
      font-size: 13px;
      color: #bbb;
      font-style: italic;
    }}

    .footer {{
      text-align: center;
      padding: 24px;
      font-size: 12px;
      color: #bbb;
    }}

    @media (max-width: 600px) {{
      .card-header {{
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
      }}
      .stats-bar {{
        gap: 20px;
      }}
    }}
  </style>
</head>
<body>

  <div class="header">
    <h1>ライバー管理レポート</h1>
    <p class="subtitle">生成日時: {now}</p>
  </div>

  <div class="stats-bar">
    <div class="stat-item">
      <span class="stat-label">登録ライバー数</span>
      <span class="stat-value">{total}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">要フォロー（1週間超）</span>
      <span class="stat-value warning">{warning_count}</span>
    </div>
  </div>

  <div class="container">
    {rows_html if rows_html else '<p style="text-align:center;color:#aaa;padding:40px;">ライバーが登録されていません。</p>'}
  </div>

  <div class="footer">
    ライバー管理システム &mdash; 最終連絡日が古い順に表示
  </div>

</body>
</html>"""

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"レポート生成: {REPORT_FILE}")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "--report":
        generate_html()
        return

    if len(args) < 2:
        print("使い方: python manage.py \"名前\" \"やり取り内容\"")
        sys.exit(1)

    name = args[0]
    content = args[1]
    update_liver(name, content)
    generate_html()


if __name__ == "__main__":
    main()
