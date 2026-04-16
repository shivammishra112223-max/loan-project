function validateLogin(){

let username = document.getElementById("username").value.trim();
let password = document.getElementById("password").value;

let errorMsg = document.getElementById("errorMsg");
errorMsg.innerText = "";

// Username check
if(username.length < 4){
    errorMsg.innerText = "Username must be at least 4 characters.";
    return false;
}

// Password check
if(password.length < 6){
    errorMsg.innerText = "Password must be at least 6 characters.";
    return false;
}

return true;
}


function validateRegister(){

let fullName = document.getElementById("full_name").value.trim();
let username = document.getElementById("username").value.trim();
let email = document.getElementById("email").value.trim();
let mobile = document.getElementById("mobile").value.trim();
let password = document.getElementById("password").value;
let confirmPassword = document.getElementById("confirm_password").value;
let city = document.getElementById("city").value.trim();

let errorMsg = document.getElementById("errorMsg");
errorMsg.innerText = "";

// Full Name
if(fullName.length < 3){
    errorMsg.innerText = "Full name must be at least 3 characters.";
    return false;
}

// Username
if(username.length < 4){
    errorMsg.innerText = "Username must be at least 4 characters.";
    return false;
}

// Email
let emailPattern = /^[^ ]+@[^ ]+\.[a-z]{2,3}$/;
if(!email.match(emailPattern)){
    errorMsg.innerText = "Enter valid email address.";
    return false;
}

// Mobile
if(mobile.length !== 10 || isNaN(mobile)){
    errorMsg.innerText = "Mobile number must be 10 digits.";
    return false;
}

// Password
if(password.length < 6){
    errorMsg.innerText = "Password must be at least 6 characters.";
    return false;
}

// Confirm Password
if(password !== confirmPassword){
    errorMsg.innerText = "Passwords do not match.";
    return false;
}

// City
if(city.length < 2){
    errorMsg.innerText = "City name too short.";
    return false;
}

return true;
}
