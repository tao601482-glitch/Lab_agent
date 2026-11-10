import { ref } from 'vue'
import { getUserInfo, setToken, setUserInfo, logout as clearLoginStorage } from './auth'

const userInfo = ref(getUserInfo())

export function useUser() {
  function saveLoginData(data) {
    setToken(data.token)
    setUserInfo(data.user)
    userInfo.value = data.user
  }

  function updateUser(user) {
    setUserInfo(user)
    userInfo.value = user
  }

  function reloadUser() {
    userInfo.value = getUserInfo()
  }

  function logout() {
    clearLoginStorage() // 删除 localStorage 中的 token 和用户信息
    userInfo.value = null // 清空页面使用的用户信息
  }

  return {
    userInfo,
    saveLoginData,
    updateUser,
    reloadUser,
    logout
  }
}
