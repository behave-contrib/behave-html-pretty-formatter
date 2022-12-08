function collapsible_toggle(id) {
    var elem = document.getElementById(id);
    var visible_display = "block";
    if (id.indexOf("table") >= 0) {
        visible_display = "contents";
    }
    elem.style.display = (elem.style.display == "none" ? visible_display : "none");
};

function collapsible_summary(id) {
    var elem = document.getElementById(id);
    var visible_display = "flex";
    elem.style.display = (elem.style.display == "none" ? visible_display : "none");
};


function expander(action) {
    var elem = Array.from(document.getElementsByClassName("scenario-capsule"));
    elem = elem.concat(Array.from(document.getElementsByClassName("scenario-header")));
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].classList.remove("collapse")
        } else if (action == "collapse_all") {
            if (!elem[i].classList.contains("collapse")) {
                elem[i].classList.add("collapse");
            }
        } else if (action == "expand_all_failed") {
            if (!elem[i].classList.contains("passed")) {
                elem[i].classList.remove("collapse");
            } else {
                if (!elem[i].classList.contains("collapse")) {
                    elem[i].classList.add("collapse");
                }
            }
        }
    }
};


function toggle_contrast_for(target_class) {
    var elements = document.getElementsByClassName(target_class);
    for(var i = 0; i < elements.length; i++) {
        if (elements[i].classList.contains("contrast")) {
            elements[i].classList.remove("contrast");
        } else {
            elements[i].classList.add("contrast");
        }
    }
};

function toggle_contrast() {
    var step_status_items = document.getElementsByClassName("step-status");
    for (var i=0; i < step_status_items.length; i++) {
        step_status_items[i].style.display = (step_status_items[i].style.display == "block" ? "none" : "block");
    };

    const contrast_classes = [
        "feature-title",
        "feature-summary-container",
        "feature-summary-row",
        "feature-icon",

        "scenario-header",
        "scenario-capsule",
        "scenario-tags",
        "scenario-duration",

        "step-capsule",
        "step-status",
        "step-duration",

        "messages",
        "embed_button",
        "link",
        "table",

    ];
    contrast_classes.forEach(toggle_contrast_for);
};

function detect_contrast() {
    var obj_div = document.createElement("div");
    obj_div.style.color = "rgb(31, 41, 59)"
    document.body.appendChild(obj_div);
    var col = document.defaultView ? document.defaultView.getComputedStyle(obj_div, null).color : obj_div.currentStyle.color;
    document.body.removeChild(obj_div);
    col = col.replace(/ /g, "");
    if (col !== "rgb(31,41,59)") {
        console.log("High Contrast theme detected.")
        toggle_contrast();
    }
}
