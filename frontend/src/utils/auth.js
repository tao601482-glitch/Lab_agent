// 存储token、存储用户信息、获取token、用户信息，删除token、用户信息这些作用
const TOKEN_KEY = 'token'
const USER_KEY = 'userInfo'
//获取token
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
//存储token
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}
//删除token
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}
//获取用户信息
export function getUserInfo() {
  const str = localStorage.getItem(USER_KEY)
  return str ? JSON.parse(str) : null
}
//存储用户信息
export function setUserInfo(userInfo) {
  localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
}
//删除用户信息
export function removeUserInfo() {
  localStorage.removeItem(USER_KEY)
}
//登出
export function logout() {
  removeToken()
  removeUserInfo()
}
