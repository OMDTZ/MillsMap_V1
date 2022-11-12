var form = document.getElementById('filterForm')
var form_elements = document.getElementById("filterForm").elements

 document.getElementById('filterSubmit').addEventListener("click", function(){
     event.preventDefault();

    console.log(form.elements['maleField'].checked);
    console.log(document.forms[1])
    var formData = new FormData(form[0])
    console.log('test' + formData.get('femaleField'))


     var form_elements = document.getElementById("filterForm").elements 
    alert(data)
    console.log(data)

    var form_data = new FormData(data[0])
    alert(data.get('male'))
});
