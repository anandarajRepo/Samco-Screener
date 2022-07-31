$(document).ready(function () {

    $('#sector-dropdown').on('change', function () {
        $("#sub-category-dropdown").html("");
        var sectorName = $(this).val();
        console.log(sectorName)
        $.ajax({
            url: "/fetchSubSector",
            type: "POST",
            data: {
                sectorName: sectorName
            },
            cache: false,
            success: function (data) {
                var output = "";
                console.log(data.subsector)
                output += "<option value=''>Choose Sub-Sector</option>"
                $.each(data.subsector, function (key, val) {
                    output += "<option value='" + val + "'>" + val + "</option>"
                });
                $("#sub-category-dropdown").append(output);
            }
        });
    });
    
});