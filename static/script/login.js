//要操作的按钮
const container=document.querySelector('.container');
const btn_login=document.querySelector('.btn-login');

//登录按钮点击事件
btn_login.addEventListener('click',function(){
    container.classList.add('success');
})