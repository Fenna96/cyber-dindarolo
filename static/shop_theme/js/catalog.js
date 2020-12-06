function increment(current) {
        quantity = document.getElementById(current);
        max_quantity = document.getElementById("max_quantity"+current).value;
        counter = quantity.value;
        counter++;
        if (counter <= max_quantity){
            quantity.setAttribute("value",counter);
            quantity.style.width = ((quantity.value.length + 1) * 8) + 'px';
        }
    }

    function decrement(current) {
        quantity = document.getElementById(current);
        counter = quantity.value;
        counter--;
        if (counter > 0){
            quantity.setAttribute("value",counter);
            quantity.style.width = ((quantity.value.length + 1) * 8) + 'px';
        }
    }

    function collapse(div){
        div.style.display = 'none';
        icon = document.getElementById(div.id+"_hide");
        icon.setAttribute("class","fa fa-caret-square-o-down");
        icon.setAttribute("onclick","expand("+div.id+")");
    }

    function expand(div){
        div.style.display = 'flex';
        icon = document.getElementById(div.id+"_hide");
        icon.setAttribute("class","fa fa-caret-square-o-up");
        icon.setAttribute("onclick","collapse("+div.id+")");
    }