$(function() {
    $(".rangeParameter").each(function() {
        var input  = $(this).find("input")[0];
        var slider = $(this).find(".slider")[0];
        var min    = parseFloat($(this).find(".rangeStart")[0].value);
        var max    = parseFloat($(this).find(".rangeEnd")[0].value);
        var step   = parseFloat($(this).find(".step")[0].value);
        var tmp = $(input).val().split("-",1);
        if(tmp.length == 2) {
            var startRange = parseFloat(tmp[0]);
            var endRange   = parseFloat(tmp[1]);
        } else {
            var startRange = min;
            var endRange   = max;
        }
        $(slider).slider({
            range:  true,
            min:    min,
            max:    max,
            step:   step,
            values: [startRange, endRange],
            slide: function(e, ui) {
                $(input).val('' + ui.values[0] + '-' + ui.values[1]);
            }
        });

        $(input).val($(slider).slider("values", 0) + '-' + $(slider).slider("values", 1));
    });

    $(".floatSliderParameter").each(function() {
        var input  = $(this).find("input")[0];
        var slider = $(this).find(".slider")[0];
        var min    = parseFloat($(this).find(".rangeStart")[0].value);
        var max    = parseFloat($(this).find(".rangeEnd")[0].value);
        var step   = parseFloat($(this).find(".step")[0].value);

        var startValue = parseFloat($(input).val());
        if(isNaN(startValue)) { // NAN
            startValue = min;
        }

        $(slider).slider({
            min:    min,
            max:    max,
            step:   step,
            value:  startValue,
            slide: function(e, ui) {
                $(input).val(ui.value);
            }
        });

        $(input).val($(slider).slider( "option", "value"));
    });
});
