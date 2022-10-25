function collapsible_toggle(id) {
    var elem = document.getElementById(id);
    var visible_display = "block";
    if (id.indexOf("table") >= 0) {
        visible_display = "contents";
    }
    elem.style.display = (elem.style.display == "none" ? visible_display : "none");
    return false;
};


function toggle_contrast_for(target_class) {
    var elements = document.getElementsByClassName(target_class);
    for(var i = 0; i < elements.length; i++) {
        if (document.getElementsByClassName(target_class)[i].classList.contains("contrast")) {
            document.getElementsByClassName(target_class)[i].classList.remove("contrast");
        } else {
            document.getElementsByClassName(target_class)[i].classList.add("contrast");
        }
    }
};

function toggle_contrast(id) {
    var step_status_items = document.getElementsByClassName("step-status");
    for (var i=0; i < step_status_items.length; i++) {
        step_status_items[i].style.display = (step_status_items[i].style.display == "block" ? "none" : "block");
    };

    var icon_items = document.getElementsByClassName("feature-panel-icon");
    icon_items[0].style.display = (icon_items[0].style.display == "none" ? "flex" : "none");


    const contrast_classes = [
        "feature-panel",

        "scenario-capsule scenario-capsule-passed",
        "scenario-capsule scenario-capsule-failed",
        "scenario-capsule scenario-capsule-undefined",
        "scenario-tags",
        "scenario-duration",

        "step-capsule step-capsule-passed",
        "step-capsule step-capsule-failed",
        "step-capsule step-capsule-undefined",
        "step-capsule step-capsule-skipped",
        "step-capsule step-capsule-commentary",
        "step-status",
        "step-duration",

        "messages",
        "embed_button",
        "link",

    ];
    contrast_classes.forEach(toggle_contrast_for);
};