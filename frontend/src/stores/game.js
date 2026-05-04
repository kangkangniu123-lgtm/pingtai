import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGameStore = defineStore('game', () => {
  // 游戏分类数据
  const categories = [
    {
      id: 1,
      name: '热门',
      type: 'hot'
    },
    {
      id: 2,
      name: '手游',
      type: 'mobile'
    },
    {
      id: 3,
      name: '端游',
      type: 'pc'
    }
  ]

  // 游戏列表
  const games = [
    {
      id: 1,
      name: 'PUBG M',
      category: 'hot',
      icon: 'https://via.placeholder.com/150?text=PUBG+M',
      description: '极速发货 24小时服务 官方ID验证',
      products: [
        {
          id: 101,
          name: '通行证(LV1-100)',
          price: 92.00,
          image: 'https://via.placeholder.com/200?text=Product+1'
        },
        {
          id: 102,
          name: '通行证PLUS(LV1-100)',
          price: 235.00,
          image: 'https://via.placeholder.com/200?text=Product+2'
        },
        {
          id: 103,
          name: '通行证(LV1-50)',
          price: 45.00,
          image: 'https://via.placeholder.com/200?text=Product+3'
        }
      ]
    },
    {
      id: 2,
      name: '和平精英',
      category: 'hot',
      icon: 'https://via.placeholder.com/150?text=Peace+Elite',
      description: '极速发货 24小时服务 官方ID验证',
      products: [
        {
          id: 201,
          name: 'UC充值 300',
          price: 30.00,
          image: 'https://via.placeholder.com/200?text=UC+300'
        },
        {
          id: 202,
          name: 'UC充值 600',
          price: 60.00,
          image: 'https://via.placeholder.com/200?text=UC+600'
        }
      ]
    },
    {
      id: 3,
      name: '王者荣耀',
      category: 'mobile',
      icon: 'https://via.placeholder.com/150?text=Honor+of+Kings',
      description: '极速发货 24小时服务 官方ID验证',
      products: [
        {
          id: 301,
          name: '点券 500',
          price: 50.00,
          image: 'https://via.placeholder.com/200?text=Points+500'
        },
        {
          id: 302,
          name: '点券 1000',
          price: 100.00,
          image: 'https://via.placeholder.com/200?text=Points+1000'
        }
      ]
    },
    {
      id: 4,
      name: '原神',
      category: 'mobile',
      icon: 'https://via.placeholder.com/150?text=Genshin',
      description: '极速发货 24小时服务 官方ID验证',
      products: [
        {
          id: 401,
          name: '原晶 180',
          price: 12.00,
          image: 'https://via.placeholder.com/200?text=Primogem+180'
        },
        {
          id: 402,
          name: '原晶 300',
          price: 20.00,
          image: 'https://via.placeholder.com/200?text=Primogem+300'
        }
      ]
    }
  ]

  // 获取分类游戏
  const getGamesByCategory = (category) => {
    return games.filter(game => game.category === category)
  }

  // 获取游戏详情
  const getGameById = (id) => {
    return games.find(game => game.id === id)
  }

  return {
    categories,
    games,
    getGamesByCategory,
    getGameById
  }
})
