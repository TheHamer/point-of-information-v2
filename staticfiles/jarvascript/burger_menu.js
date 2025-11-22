function burgerDropdown() {
    const dropElement = document.querySelector(".drop-contents")
    const burgerIcon = document.querySelector(".burger-icon")

    if (dropElement.style.display === "block") {
        dropElement.style.display = "none"
        burgerIcon.style.color = "#7F00FF"
    }else{
        dropElement.style.display = "block"
        burgerIcon.style.color = "#BF40BF"
    }
}