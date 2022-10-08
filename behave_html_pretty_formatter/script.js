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

    const contrast_classes = [
        "embed",
        "test-tags",
        "suite-info",
        "suite-status",
        "suite-name",
        "suite-time",
        "scenario-capsule scenario-capsule-passed",
        "scenario-capsule scenario-capsule-failed",
        "scenario-capsule scenario-capsule-undefined",
        "scenario-time",
        "messages-passed",
        "messages-passed-last",
        "messages-failed",
        "messages-failed-last",
        "messages-undefined",
        "messages-undefined-last",
        "step-capsule step-capsule-pass",
        "step-capsule step-capsule-fail",
        "step-capsule step-capsule-undefined",
        "step-capsule step-capsule-skip-not-started",
        "step-capsule step-capsule-commentary",
        "step-decorator-plus-duration",
        "step-status",
        "step-decorator",
        "test-duration",
        "step-duration",
        "step-link",
        "link",
    ];
    contrast_classes.forEach(toggle_contrast_for);
};