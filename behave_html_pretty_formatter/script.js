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
    var elem = document.getElementsByClassName("scenario-capsule");
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].style.padding = "1rem";
        } else if (action == "collapse_all") {
            elem[i].style.padding = "5px";
            elem[i].style.margin = "5px 0";
        } else if (action == "expand_all_failed") {
            if (!elem[i].classList.contains("passed")) {
                elem[i].style.padding = "1rem";
            }
        }
    }

    var elem = document.getElementsByClassName("step-capsule");
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].style.display = "flex"
        } else if (action == "collapse_all") {
            elem[i].style.display = "none";
        } else if (action == "expand_all_failed") {
            var scenario_capsule = elem[i].closest(".scenario-capsule")
            if (!scenario_capsule.classList.contains("passed")) {
                elem[i].style.display = "flex";
            }
        }
    }

    var elem = document.getElementsByClassName("messages");
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].style.display = "inherit"
        } else if (action == "collapse_all") {
            elem[i].style.display = "none";
        } else if (action == "expand_all_failed") {
            var scenario_capsule = elem[i].closest(".scenario-capsule")
            if (!scenario_capsule.classList.contains("passed")) {
                elem[i].style.display = "inherit";
            }
        }
    }

    var elem = document.getElementsByClassName("scenario-tags");
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].style.display = "inline-block";
        } else if (action == "collapse_all") {
            elem[i].style.display = "none";
        } else if (action == "expand_all_failed") {
            var scenario_capsule = elem[i].closest(".scenario-capsule")
            if (!scenario_capsule.classList.contains("passed")) {
                elem[i].style.display = "inline-block";
            }
        }
    }

    var elem = document.getElementsByClassName("scenario-name");
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].style.paddingBottom = "0.5rem";
        } else if (action == "collapse_all") {
            elem[i].style.paddingBottom = "0";
        } else if (action == "expand_all_failed") {
            var scenario_capsule = elem[i].closest(".scenario-capsule")
            if (!scenario_capsule.classList.contains("passed")) {
                elem[i].style.paddingBottom = "0.5rem";
            }
        }
    }

    var elem = document.getElementsByClassName("scenario-duration");
    for(var i = 0; i < elem.length; i++) {
        if (action == "expand_all") {
            elem[i].style.fontSize = "0.75rem";
        } else if (action == "collapse_all") {
            elem[i].style.fontSize = "inherit";
        } else if (action == "expand_all_failed") {
            var scenario_capsule = elem[i].closest(".scenario-capsule")
            if (!scenario_capsule.classList.contains("passed")) {
                elem[i].style.fontSize = "0.75rem";
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

function toggle_contrast(id) {
    var step_status_items = document.getElementsByClassName("step-status");
    for (var i=0; i < step_status_items.length; i++) {
        step_status_items[i].style.display = (step_status_items[i].style.display == "block" ? "none" : "block");
    };

    const contrast_classes = [
        "feature-title",
        "feature-summary-container",
        "feature-summary-row",
        "feature-icon",

        "scenario-capsule",
        "scenario-tags",
        "scenario-duration",

        "step-capsule",
        "step-status",
        "step-duration",

        "messages",
        "embed_button",
        "link",

    ];
    contrast_classes.forEach(toggle_contrast_for);
};