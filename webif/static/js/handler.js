var selectedDevice;


//***************************************************
//Function to store manual inserted cookie - File
//***************************************************
function BtnStoreCookie()
{
	data = myCodeMirrorConf.getValue()
	data=JSON.stringify(data)
	data = data.split('\"').join("")
	$.ajax({
		url: "storecookie.html",
		type: "GET",
		data: { cookie_txt : data }, //data,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
			myResult=JSON.parse(response)
			if (myResult.data.Result == true)
				{
				document.getElementById('txt_Result').textContent='You did it\nLogin was successfull\nCookie was stored\nPlease reload Page'
				document.getElementById('txt_Result').style.backgroundColor="Lightgreen"
				document.getElementById('txt_Result').style.color='black'
				}
			else
				{
				document.getElementById('txt_Result').textContent='Sorry, login was not successfull\nCookie was not stored\nPlease try again'
				document.getElementById('txt_Result').style.backgroundColor="Red"
				document.getElementById('txt_Result').style.color='black'
				}
		},
		error: function (xhr, status, error) {
			document.getElementById("txt_Result").innerHTML = "Error while Communication !";
            $("#reload-element").removeClass("fa-spin");
            $("#MFAcardOverlay").hide();
		}
	});	
}


//***************************************************
// Function to communicate with the plugin himself
//***************************************************
function PublicAjax(url, data)
{
	//data = unescape(encodeURIComponent(JSON.stringify(data)))
	data=JSON.stringify(data)
	$.ajax({
		url: url + ".html",
		type: "GET",
		data: { data : data }, //data,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
				ValidateMFAResponse(response);
		},
		error: function (xhr, status, error) {
			document.getElementById("Tooltip").innerHTML= "<div><strong>Error</strong><br><br>Error while Communication !</div>"
		    document.getElementById("Tooltip").style.backgroundColor="red"
	    	 
			
			$("#reload-element").removeClass("fa-spin");
            $("#MFAcardOverlay").hide();
		}
	});	
}



//*******************************************
// Button Handler for saving Commandlet
//*******************************************

function BtnSave(result)
{
    document.getElementById("txtresult").value = "";


    if (document.getElementById("txtCmdName").value == "")
	{
 	  alert ("No Name given for CommandLet, please enter one");
	  return;
	}
    if (document.getElementById("txtApiUrl").value == "")
	{
 	  alert ("No API-URL given for CommandLet, please enter one");
	  return;
	}

    document.getElementById("txtButton").value ="BtnSave";

    myPayload = myCodeMirrorPayload.getValue();
    StoreCMD
	(
         document.getElementById("txtValue").value,
         document.getElementById("selectedDevice").value,
         myPayload,
         document.getElementById("txtCmdName").value,
         document.getElementById("txtApiUrl").value,
         document.getElementById("txtDescription").value,
         document.getElementById("txtmyReqType").value
	);

}

//*******************************************
// Button Handler for checking Json
//*******************************************

function BtnCheck(result)
{

    document.getElementById("txtButton").value ="BtnCheck";
    try {
	// Block of code to try
	myValue = document.getElementById("txtValue").value
	myPayload = myCodeMirrorPayload.getValue();
	myPayload = myPayload.replace("<mValue>",myValue);
	var myTest = JSON.stringify(JSON.parse(myPayload),null,2)
	myCodeMirrorPayload.setValue(myTest);
	myCodeMirrorPayload.focus;
	myCodeMirrorPayload.setCursor(myCodeMirrorPayload.lineCount(),0);
	document.getElementById("txtresult").value = "JSON-Structure is OK";
	document.getElementById("resultOK").style.visibility="visible";
	document.getElementById("resultNOK").style.visibility="hidden";
	
        }
    catch(err) {
         // Block of code to handle errors
	document.getElementById("txtresult").value = "JSON-Structure is not OK\n"+err;
	document.getElementById("resultOK").style.visibility="hidden";
	document.getElementById("resultNOK").style.visibility="visible";
	} 
}

//*******************************************
// Button Handler for testing
//*******************************************

function BtnTest(result)
{
   selectedDevice = document.getElementById("selectedDevice").value;

    if (selectedDevice == "no Device selected")
	{
 	  alert ("No Device selected for Test, first select one");
	  return;
	}
    txtValue = document.getElementById("txtValue").value;
    if (txtValue == "")
	{
 	  alert ("No Value set to send, please enter value");
	  return;
	}

    document.getElementById("txtButton").value ="BtnTest";
    myPayload = myCodeMirrorPayload.getValue();

    TestCMD
	(
         document.getElementById("txtValue").value,
         document.getElementById("selectedDevice").value,
         myPayload,
         document.getElementById("txtCmdName").value,
         document.getElementById("txtApiUrl").value,
         document.getElementById("txtDescription").value,
         document.getElementById("txtmyReqType").value
	);
}

//*******************************************
// Button Handler for deleting
//*******************************************

function BtnDelete(result)
{
    var filetodelete = document.getElementById("txtCmdName").value;
    if (filetodelete == "") {
         alert ("No Command selected to delete, first select one");
         return;
        }
    filetodelete=filetodelete+".cmd";
    var r = confirm("Your really want to delete\n\n"+ filetodelete + "\n\nContinue ?");
    if (r == false) {
        return;
        } 
    document.getElementById("txtButton").value ="BtnDelete";
    DeleteCMD
	(
         document.getElementById("txtValue").value,
         document.getElementById("selectedDevice").value,
         "",
         document.getElementById("txtCmdName").value,
         document.getElementById("txtApiUrl").value,
         document.getElementById("txtDescription").value,
         ""
	);
}


//*************************************************************
// ValidateLoginResponse -checks the login-button
//*************************************************************

function ValidateLoginResponse(response)
{
var myResult = ""
var temp = ""
var objResponse = JSON.parse(response)
for (x in objResponse)
    {
     temp = temp + objResponse[x]+"\n";
    }

document.getElementById("txt_Result").innerHTML = temp;
}

//*************************************************************
// ValidateEncodeResponse -checks the login-button
//*************************************************************

function ValidateEncodeResponse(response)
{
var myResult = ""
var temp = ""
var objResponse = JSON.parse(response)
for (x in objResponse)
    {
     if (x == "0")
 	{
	  document.getElementById("txtEncoded").value = objResponse[x].substr(8);	  
	}
     else
	{
	  temp = temp + objResponse[x]+"\n";
	}
    }

document.getElementById("txt_Result").value = temp;
}



//*************************************************************
// ValidateResponse - checks the response for button-Actions
//*************************************************************

function ValidateResponse(response)
{
var myResult = ""
var temp = ""
var objResponse = JSON.parse(response)
for (x in objResponse[0])
    {
      if (x == "Status") {
	  myResult = objResponse[0][x];
	}
      else {
          temp = temp + objResponse[0][x]+"\n";
        }
    }

document.getElementById("txtresult").value = temp;
if (myResult == "OK")
{
 document.getElementById("resultOK").style.visibility="visible";
 document.getElementById("resultNOK").style.visibility="hidden";
 reloadCmds();
}
else
{
 document.getElementById("resultOK").style.visibility="hidden";
 document.getElementById("resultNOK").style.visibility="visible";
}

}

//*******************************************
// Function to Test Command-Let
//*******************************************

function TestCMD(txtValue,selectedDevice,txt_payload,txtCmdName,txtApiUrl,txtDescription, txtmyReqType) {
	$.ajax({
		url: "handle_buttons.html",
		type: "GET",
		data: { txtValue : txtValue,
			selectedDevice:selectedDevice,
			txtButton : "BtnTest",
			txt_payload : txt_payload,
			txtCmdName : txtCmdName,
			txtApiUrl : txtApiUrl,
			txtDescription : txtDescription,
			txtmyReqType : txtmyReqType,} ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
				ValidateResponse(response)
		},
		error: function () {
			document.getElementById("txtresult").value = "Error while Communication !";
			document.getElementById("resultOK").style.visibility="hidden";
			document.getElementById("resultNOK").style.visibility="visible";
		}
	});
  return
}

//*******************************************
// Function to Save Command-Let
//*******************************************

function StoreCMD(txtValue,selectedDevice,txt_payload,txtCmdName,txtApiUrl,txtDescription,txtmyReqType) {
	$.ajax({
		url: "handle_buttons.html",
		type: "GET",
		data: { txtValue : "",
			selectedDevice:selectedDevice,
			txtButton : "BtnSave",
			txt_payload : txt_payload,
			txtCmdName : txtCmdName,
			txtApiUrl : txtApiUrl,
			txtDescription : txtDescription,
			txtmyReqType : txtmyReqType} ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
				ValidateResponse(response)
		},
		error: function () {
			document.getElementById("txtresult").value = "Error while Communication !";
			document.getElementById("resultOK").style.visibility="hidden";
			document.getElementById("resultNOK").style.visibility="visible";
		}
	});
  return
}

//*******************************************
// Function to Delete Command-Let
//*******************************************

function DeleteCMD(txtValue,selectedDevice,txt_payload,txtCmdName,txtApiUrl,txtDescription,txtmyReqType) {
	$.ajax({
		url: "handle_buttons.html",
		type: "GET",
		data: { txtValue : "",
			selectedDevice:selectedDevice,
			txtButton : "BtnDelete",
			txt_payload : txt_payload,
			txtCmdName : txtCmdName,
			txtApiUrl : txtApiUrl,
			txtDescription : txtDescription,
			txtmyReqType : txtmyReqType} ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
				ValidateResponse(response)
		},
		error: function () {
			document.getElementById("txtresult").value = "Error while Communication !";
			document.getElementById("resultOK").style.visibility="hidden";
			document.getElementById("resultNOK").style.visibility="visible";
		}
	});
  return
}


//************************************************
// OnClick-function for Command-List
//************************************************

function SelectCmd()
{

//$("#AlexaDevices").on("click", "tr",function()
  
   var value = $(this).closest("tr").find("td").first().text();

   if (value != "") {
	alert(value);
      }
  
}

//************************************************
// builds and show table with saves Commandlets
//************************************************


function build_cmd_list(result)
{

    var temp ="";
    temp = "<div class='table-responsive' id='tableCommands' href='#' onclick='SelectCmd()'  style=min-width: 30px;><table class='table table-striped table-hover'>";
    temp = temp + "<thead><tr class='shng_heading'><th class='py-1'>Command-Name</th></tr></thead>";
    temp = temp + "<tbody>";
	
    $.each(result, function(index, element) {
        temp = temp + "<a href='SelectListItem'><tr><td class='py-1'>"+ element.Name + "</td></tr>";
    	        
    })
    temp = temp + "</tbody></table></div>";
    $('#Cmds').html(temp);

    $('#tableCommands').on("click", "tr",function()
     {
       var value = $(this).closest("tr").find("td").first().text();
       if (value != "") {
       LoadCommand(value);
     }
    });



}


//*******************************************
// reloads the list with the Command-Lets
//*******************************************
function reloadCmds()
{
        $("#reload-element").addClass("fa-spin");
        $("#cardOverlay").show();
        $.getJSON("build_cmd_list_html", function(result)
        		{
	        	build_cmd_list(result);
	            window.setTimeout(function()
	            		{
		                $("#refresh-element").removeClass("fa-spin");
		                $("#reload-element").removeClass("fa-spin");
		                $("#cardOverlay").hide();
	            		}, 300);

        		});
    
}

//*******************************************
// Load Commandlet to Web-Site
//*******************************************
function LoadCommand(txtCmdName)
{
	$.ajax({
		url: "handle_buttons.html",
		type: "GET",
		data: { txtValue : "",
			selectedDevice:"",
			txtButton : "BtnLoad",
			txt_payload : "",
			txtCmdName : txtCmdName,
			txtApiUrl : "",
			txtDescription : "",
			txtmyReqType : ""} ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
				ShowCommand(response,txtCmdName);
		},
		error: function () {
			document.getElementById("txtresult").value = "Error while Communication !";
			document.getElementById("resultOK").style.visibility="hidden";
			document.getElementById("resultNOK").style.visibility="visible";
		}
	});
  return
}

//*******************************************
// Load 2 Fields
//*******************************************
function ShowCommand(response,txtCmdName)
{
	var myResult = ""
	var temp = ""
	var objResponse = JSON.parse(response)
  	document.getElementById("txtCmdName").value = txtCmdName;		
	for (x in objResponse[0])
	    {
	      if (x == "Status")
		{
		  myResult = objResponse[0][x];
		}
	     else if (x == "Description")
 		{
		 console.log(objResponse[0][x])
		 var test = objResponse[0][x];

	  	 document.getElementById("txtDescription").value = objResponse[0][x];		
		}
	     else if (x == "myUrl")
		{
		   console.log(objResponse[0][x])
	  	 document.getElementById("txtApiUrl").value = objResponse[0][x];		
		}
	     else if (x == "payload")
		{
		 myjson = objResponse[0][x].split("'").join("\"");
		 myjson = myjson.split("\\").join("");
		 var myTest = JSON.stringify(JSON.parse(myjson),null,2)
 	   myCodeMirrorPayload.setValue(myTest);
	   myCodeMirrorPayload.focus;
		 myCodeMirrorPayload.setCursor(myCodeMirrorPayload.lineCount(),0);
		}
	     else if (x == "myReqType")
		{
		   console.log(objResponse[0][x])
	  	 document.getElementById("txtmyReqType").value = objResponse[0][x];		
		}		
	    }
	document.getElementById("txtresult").value = myResult;
	if (myResult == "OK")
	{
	 document.getElementById("resultOK").style.visibility="visible";
	 document.getElementById("resultNOK").style.visibility="hidden";
	 reloadCmds();
	}
	else
	{
	 document.getElementById("resultOK").style.visibility="hidden";
	 document.getElementById("resultNOK").style.visibility="visible";
	}
}


//************************************************
// builds and show table with Routines
//************************************************


function build_routine_list(result)
{

    var temp ="";
    temp = "<div class='table-responsive' id='tableRoutines' href='#' onclick='SelectRoutine()'  style=min-width: 30px;><table class='table table-striped table-hover'>";
    temp = temp + "<thead><tr class='shng_heading'><th class='py-1'>Routine-Name</th></tr></thead>";
    temp = temp + "<tbody>";
	  
    for (var i = 0; i < result.length; i++){
        temp = temp + "<a href='SelectListItem'><tr><td class='py-1'>"+ result[i] + "</td></tr>";
    	        
    }
	

    temp = temp + "</tbody></table></div>";
    $('#routines').html(temp);

    $('#tableRoutines').on("click", "tr",function()
     {
       var value = $(this).closest("tr").find("td").first().text();
       if (value != "") {
       //LoadCommand(value);
       loadRoutine(value);
     }
    });



}
//*******************************************
// reloads the list with the Command-Lets
//*******************************************
function reloadRoutines()
{
        $("#reload-element").addClass("fa-spin");
        $("#cardOverlay").show();
        $.getJSON("build_routine_list_html", function(result)
        		{
	        	build_routine_list(result);
	            window.setTimeout(function()
	            		{
		                $("#refresh-element").removeClass("fa-spin");
		                $("#reload-element").removeClass("fa-spin");
		                $("#cardOverlay").hide();
	            		}, 300);

        		});

}

//***************************************************
//Function to load a single Routine
//***************************************************
function loadRoutine(routineName)
{
	$.ajax({
		url: "load_routine.html",
		type: "GET",
		data: { name : routineName }, //data,
		contentType: "application/json; charset=utf-8",
		success: function (response) {
			myResult=JSON.parse(response)
			if (myResult.Result == true)
				{
				myCodeMirrorRoutines.setValue(JSON.stringify(JSON.parse(myResult.data),null,2))
				}
			else
				{

				}
		},
		error: function (xhr, status, error) {
			document.getElementById("txt_routine").innerHTML = "Error while Communication !";
            $("#reload-element").removeClass("fa-spin");
		}
	});	
}


//************************************************
// OnClick-function for Routine-List
//************************************************

function SelectRoutine()
{
   var value = $(this).closest("tr").find("td").first().text();

   if (value != "") {
	alert(value);
      }
  
}

//************************************************
// Refresh Cookie manual
//************************************************

function Refresh_Cookie()
{
	$.ajax({
		url: "refresh_cookie.html",
		type: "GET",
		data: {}, 
		contentType: "application/json; charset=utf-8",
		success: function (response) {
			myResult=JSON.parse(response)
			if (myResult.Result == true)
				{
				  myCodeMirrorConf.setValue(myResult.data)
				  document.getElementById('webif-head-span-3-2').innerHTML = myResult.login_info
				  document.getElementById('webif-head-span-1-2').innerHTML = myResult.csrf
				}
			else
				{

				}
		},
		error: function (xhr, status, error) {
            myCodeMirrorConf.setValue("Error while Communication !");
            $("#reload-element").removeClass("fa-spin");
		}
	});	
}
	
