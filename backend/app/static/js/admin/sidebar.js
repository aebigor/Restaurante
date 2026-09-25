const sidebar=document.getElementById("sidebar");
const btn=document.getElementById("toggleSidebar");
btn?.addEventListener("click",()=>sidebar?.classList.toggle("closed"));
document.getElementById("logoutBtn")?.addEventListener("click",(e)=>{
    e.preventDefault();
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.replace("/admin/login");
});
