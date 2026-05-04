<template>
  <div class="page-container order-page">
    <!-- 返回按钮 -->
    <div class="header">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="title">确认订单</h1>
      <div class="placeholder"></div>
    </div>

    <!-- 订单商品信息 -->
    <div class="section">
      <h3 class="section-title">订单商品</h3>
      <div v-for="item in cartStore.items" :key="`${item.product.id}-${item.gameId}`" class="product-item">
        <img :src="item.product.image" :alt="item.product.name" class="product-thumb" />
        <div class="product-details">
          <p class="product-game">{{ item.gameName }}</p>
          <p class="product-name">{{ item.product.name }}</p>
          <p class="product-price">¥{{ item.product.price.toFixed(2) }}</p>
        </div>
        <div class="product-quantity">
          <button @click="decreaseQuantity(item)">−</button>
          <span>{{ item.quantity }}</span>
          <button @click="increaseQuantity(item)">+</button>
        </div>
      </div>
    </div>

    <!-- 收货信息 -->
    <div class="section">
      <h3 class="section-title">收货信息</h3>
      <div class="form-group">
        <label class="form-label">
          <span class="required">*</span>
          手机号
        </label>
        <input
          v-model="orderForm.phone"
          type="tel"
          placeholder="请输入本人有效的手机号"
          class="form-input"
        />
      </div>
    </div>

    <!-- 账户信息 -->
    <div class="section">
      <h3 class="section-title">账户信息</h3>
      <div class="form-group">
        <label class="form-label">
          <span class="required">*</span>
          玩家ID
        </label>
        <input
          v-model="orderForm.playerId"
          type="text"
          placeholder="请输入游戏玩家ID"
          class="form-input"
        />
      </div>
      <div class="form-group">
        <label class="form-label">
          <span class="required">*</span>
          角色昵称
        </label>
        <input
          v-model="orderForm.characterName"
          type="text"
          placeholder="请输入角色昵称"
          class="form-input"
        />
      </div>
    </div>

    <!-- 订单总额 -->
    <div class="order-total">
      <span>合计：</span>
      <span class="total-price">¥{{ cartStore.totalPrice.toFixed(2) }}</span>
    </div>

    <!-- 提交按钮 -->
    <div class="order-actions">
      <button class="btn btn-primary btn-block" @click="submitOrder">
        提交订单
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { useUserStore } from '../stores/user'

const router = useRouter()
const cartStore = useCartStore()
const userStore = useUserStore()

const orderForm = reactive({
  phone: '',
  playerId: '',
  characterName: ''
})

const goBack = () => {
  router.back()
}

const increaseQuantity = (item) => {
  cartStore.updateQuantity(item.product.id, item.gameId, item.quantity + 1)
}

const decreaseQuantity = (item) => {
  if (item.quantity > 1) {
    cartStore.updateQuantity(item.product.id, item.gameId, item.quantity - 1)
  }
}

const submitOrder = () => {
  // 验证表单
  if (!orderForm.phone || !orderForm.playerId || !orderForm.characterName) {
    alert('请填写完整的订单信息')
    return
  }

  if (cartStore.items.length === 0) {
    alert('购物车为空')
    return
  }

  // 创建订单
  const orderData = {
    items: cartStore.items,
    ...orderForm,
    totalPrice: cartStore.totalPrice
  }

  // 保存订单到本地存储
  sessionStorage.setItem('currentOrder', JSON.stringify(orderData))

  // 跳转到支付页
  router.push('/payment')
}
</script>

<style scoped>
.order-page {
  padding: 0;
  background-color: var(--bg-color);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: white;
  position: sticky;
  top: 0;
  z-index: 50;
}

.back-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: var(--text-color);
  cursor: pointer;
  padding: 0;
}

.title {
  flex: 1;
  text-align: center;
  font-size: 16px;
  font-weight: 600;
}

.placeholder {
  width: 28px;
}

.section {
  background-color: white;
  padding: 16px;
  margin: 8px 0;
  border-radius: 4px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 12px;
}

.product-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background-color: var(--bg-color);
  border-radius: 6px;
  align-items: center;
  margin-bottom: 8px;
}

.product-thumb {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  object-fit: cover;
  flex-shrink: 0;
}

.product-details {
  flex: 1;
  min-width: 0;
}

.product-game {
  font-size: 12px;
  color: var(--text-light);
  margin-bottom: 2px;
}

.product-name {
  font-size: 13px;
  color: var(--text-color);
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-price {
  font-size: 14px;
  color: var(--danger-color);
  font-weight: 600;
}

.product-quantity {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: white;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 4px 8px;
}

.product-quantity button {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--primary-color);
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-quantity span {
  min-width: 20px;
  text-align: center;
  font-size: 13px;
}

.form-group {
  margin-bottom: 12px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
}

.required {
  color: var(--danger-color);
  margin-right: 4px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.form-input:focus {
  border-color: var(--primary-color);
}

.order-total {
  background-color: white;
  padding: 16px;
  margin: 8px 0;
  text-align: right;
  font-size: 16px;
  font-weight: 600;
  border-top: 2px solid var(--border-color);
}

.total-price {
  color: var(--danger-color);
  font-size: 20px;
  margin-left: 8px;
}

.order-actions {
  padding: 16px;
  background-color: white;
  border-top: 1px solid var(--border-color);
}

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 16px;
}
</style>
