from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 用於 flash 訊息

class FridgeInventory:
    def __init__(self, filename='fridge_inventory.json'):
        self.filename = filename
        self.inventory = self.load_inventory()

    def load_inventory(self):
        """從 JSON 檔案載入食材庫存"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def save_inventory(self):
        """將食材庫存保存到 JSON 檔案"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.inventory, f, ensure_ascii=False, indent=2)

    def add_item(self, name, quantity, expiry_days=7):
        """新增食材到庫存"""
        for item in self.inventory:
            if item['name'] == name:
                item['quantity'] += quantity
                item['added_date'] = datetime.now().strftime("%Y-%m-%d")
                item['expiry_date'] = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
                self.save_inventory()
                return True

        new_item = {
            'name': name,
            'quantity': quantity,
            'added_date': datetime.now().strftime("%Y-%m-%d"),
            'expiry_date': (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
        }
        self.inventory.append(new_item)
        self.save_inventory()
        return True

    def update_item_quantity(self, name, change):
        """更新食材數量（增加或減少）"""
        for item in self.inventory:
            if item['name'] == name:
                # 確保數量不會小於 0
                item['quantity'] = max(0, item['quantity'] + change)
                
                # 如果數量變為 0，則從清單中移除
                if item['quantity'] == 0:
                    self.inventory.remove(item)
                
                self.save_inventory()
                return True
        return False

    def delete_item(self, name):
        """從庫存中刪除指定食材"""
        self.inventory = [item for item in self.inventory if item['name'] != name]
        self.save_inventory()
        return True

    def get_expired_items(self):
        """獲取過期和即將過期的食材"""
        today = datetime.now()
        expired_items = []
        soon_to_expire = []

        for item in self.inventory:
            expiry_date = datetime.strptime(item['expiry_date'], "%Y-%m-%d")
            days_until_expiry = (expiry_date - today).days

            if days_until_expiry < 0:
                expired_items.append(item)
            elif days_until_expiry <= 3:
                soon_to_expire.append(item)

        return expired_items, soon_to_expire

# 創建全域 FridgeInventory 實例
fridge = FridgeInventory()

@app.route('/', methods=['GET', 'POST'])
def index():
    """主頁面，顯示當前庫存並處理新增食材"""
    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])
        expiry_days = int(request.form.get('expiry_days', 7))

        if name and quantity:
            fridge.add_item(name, quantity, expiry_days)
            flash(f'成功新增 {name} {quantity} 份', 'success')
        else:
            flash('請填寫完整資訊', 'error')

    expired_items, soon_to_expire = fridge.get_expired_items()
    return render_template('index.html', 
                           inventory=fridge.inventory, 
                           expired_items=expired_items, 
                           soon_to_expire=soon_to_expire)

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    """更新食材數量的路由"""
    name = request.form['name']
    change = int(request.form['change'])
    
    if fridge.update_item_quantity(name, change):
        flash(f'成功更新 {name} 的數量', 'success')
    else:
        flash(f'未找到 {name}', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_item', methods=['POST'])
def delete_item():
    """刪除指定食材的路由"""
    name = request.form['name']
    
    if fridge.delete_item(name):
        flash(f'成功刪除 {name}', 'success')
    else:
        flash(f'未找到 {name}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    # 確保 templates 資料夾存在
    os.makedirs('templates', exist_ok=True)
