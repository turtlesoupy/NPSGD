jQuery.validator.addMethod(
        "rangeParameter",
        function(value, element, params) {
            var tmp = $(element).val().split("-",2);
            if(tmp.length != 2) {
                return false;
            } 

            var start = parseFloat(tmp[0]);
            var end   = parseFloat(tmp[1]);

            return !(isNaN(start) || isNaN(end) || start > end || start < params[0] || end > params[1]);
        },
        jQuery.format("Please select a range between {0} and {1}")
);

jQuery.validator.addMethod(
        "integer",
        function(value, element) {
            return !isNaN(value) && parseFloat(value) == parseInt(value, 10);
        },
        "Please select a integer value"
);

jQuery.validator.addMethod(
        "integerRange",
        function(value, element, params) {
            return !isNaN(value) && parseFloat(value) == parseInt(value,10) &&
                    value >= params[0] && value <= params[1];
        },
        jQuery.format("Please select a integer value between {0} and {1}")
);

$(function() {
    $(".rangeParameter").each(function() {
        var input  = $(this).find("input")[0];
        var slider = $(this).find(".slider")[0];
        var min    = parseFloat($(input).attr('data-rangeStart'));
        var max    = parseFloat($(input).attr('data-rangeEnd'));
        var step   = parseFloat($(input).attr('data-end'));
        function inputParse() {
            var tmp = $(input).val().split("-",2);
            if(tmp.length == 2) {
                return [parseFloat(tmp[0]), parseFloat(tmp[1])];
            } else {
                return [min,max];
            }
        }

        $(slider).slider({
            range:  true,
            min:    min,
            max:    max,
            step:   step,
            values: inputParse(),
            slide: function(e, ui) {
                $(input).val('' + ui.values[0] + '-' + ui.values[1]);
            }
        });

        $(input).val($(slider).slider("values", 0) + '-' + $(slider).slider("values", 1));
        $(input).change(function() {
            $(slider).slider("values", inputParse());
        });
    });

    $(".floatSliderParameter").each(function() {
        var input  = $(this).find("input")[0];
        var slider = $(this).find(".slider")[0];
        var min    = parseFloat($(input).attr("data-rangeStart"));
        var max    = parseFloat($(input).attr("data-rangeEnd"));
        var step   = parseFloat($(input).attr("data-step"));

        function inputParse() {
            var ret = parseFloat($(input).val());
            if(isNaN(ret)) {
                ret = min;
            }

            return ret;
        }


        $(slider).slider({
            min:    min,
            max:    max,
            step:   step,
            value:  inputParse(),
            slide: function(e, ui) {
                $(input).val(ui.value);
            }
        });

        $(input).val($(slider).slider( "option", "value"));
        $(input).change(function() {
            $(slider).slider("value", inputParse());
        });
    });


    //Form validation
    rules = {
        email: {
            required: true,
            email: true
        }
    };

    $("#modelSubmit").find(".npsgdFloatRange").each(function (i,e) {
        rules[e.name] = {
            range: [parseFloat($(e).attr('data-rangeStart')), parseFloat($(e).attr("data-rangeEnd"))]
        };
    });

    $("#modelSubmit").find(".npsgdIntegerRange").each(function (i,e) {
        rules[e.name] = {
            integerRange: [parseInt($(e).attr('data-rangeStart'), 10), parseInt($(e).attr("data-rangeEnd"), 10)]
        };
    });

    $("#modelSubmit").find(".npsgdInteger").each(function (i,e) {
        var r = { integer: true};
        var rStart = parseFloat($(e).attr("data-rangeStart"));
        var rEnd   = parseFloat($(e).attr("data-rangeEnd"));
        if(!isNaN(rStart)) {
            r['min'] = rStart; 
        }
        if(!isNaN(rEnd)) {
            r['max'] = rStart; 
        }
        rules[e.name] = r;
    });

    $("#modelSubmit").find(".npsgdFloat").each(function (i,e) {
        var r = {};
        var rStart = parseFloat($(e).attr("data-rangeStart"));
        var rEnd   = parseFloat($(e).attr("data-rangeEnd"));
        if(!isNaN(rStart)) {
            r['min'] = rStart; 
        }
        if(!isNaN(rEnd)) {
            r['max'] = rStart; 
        }
        rules[e.name] = r;
    });

    $("#modelSubmit").find(".npsgdRange").each(function (i,e) {
        rules[e.name] = {
            rangeParameter: [parseFloat($(e).attr('data-rangeStart')), parseFloat($(e).attr("data-rangeEnd"))]
        };
    });



    $("#modelSubmit").validate({
        rules: rules        
    });


    //Tooltips (parameter help)
    $('.modelParameterHelp').each(function(i,e) {
        var content = $(e).attr('data-helpText');
        $(e).qtip({
            content: content
        });
        $(e).click(function(){return false;});
    });
});
