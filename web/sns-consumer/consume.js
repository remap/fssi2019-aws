
SQS_QUEUE_POLICY = `{
"Version": "2012-10-17",
"Id": "arn:aws:sqs:us-west-1:756428767688:Charles/SQSDefaultPolicy",
"Statement": [
{
  "Sid": "Sid1568276376397",
  "Effect": "Allow",
  "Principal": "*",
  "Action": "SQS:*",
  "Resource": "arn:aws:sqs:us-west-1:756428767688:fssi2019-consumerweb-*" 
  }
  ]
  }`; 
  
 var queueURL;
 var sqs;
 var sns;
 var checking = false; 
 var ready = false; 


//   ?exhibit=name 
var urlparams = new URLSearchParams(window.location.search); 
console.log("Could select experience", urlparams.get('experience')); 
console.log("Could select topic", urlparams.get('topic')); 
console.log("Could select title", urlparams.get('title')); 

var experience = urlparams.get('experience')==null ? "tactile" : urlparams.get('experience'); 
var title = urlparams.get('title')==null ? "Emission" : urlparams.get('title'); 
var topic = urlparams.get('topic')==null ? "fssi2019-sns-emission" : urlparams.get('topic'); 
var queueName = "fssi2019-consumerweb-" + topic + "-" + makeid(10); 

//https://cyan4973.github.io/xxHash/


function hashColor(s) { 
 	var hc; 

	if (s.length < 1) { 
		hc=0x0dead0; 
	} 
	else { 
		h = XXH.h32( s , 0xABCD ); 
		hc = Math.abs(h) & 0xFFFFFF; 
	}
	return(hc); 
	
   //  def getHashColorString(self, s):
//         return ( "%06X" % self.getHashColor(s)) 
        

} 
function hashColorArray(s) { 
	var hc = hashColor(s);  
	return [((hc & 0xFF0000) >> 16), ((hc & 0xFF00) >> 8),  (hc & 0xFF)]; 
	}
// 	
// s = "foo";
// 
// 
// console.log("#"+hashColor(s).toString(16));

function makeid(length) {
   var result           = '';
   var characters       = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
   var charactersLength = characters.length;
   for ( var i = 0; i < length; i++ ) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
   }
   return result;
}

             
             
             
 function check() {
 	 if (!ready) return; 
	 if (checking) return; 
     var params = {
         QueueUrl: queueURL,
         MaxNumberOfMessages: 10, 
         VisibilityTimeout: 5, 
         WaitTimeSeconds: 1	// long polling to avoid empty messages (though, why?) 
     };

	 checking = true; 
     sqs.receiveMessage(params, function(err, data) {
     	if (err) {
             console.log("Receive Error", err);
         } else if (data.Messages && data.Messages.length > 0) {
         
         	 // propagate all messages for now
        
             var deleteParams = {
                 QueueUrl: queueURL,
                 Entries: []
                 // ReceiptHandle: data.Messages[0].ReceiptHandle
             };
             
         	 for (const msg of data.Messages) {  // ES6 browsers only 
         	  	
         	  	console.log(msg.Body);
         	  	message = JSON.parse(JSON.parse(msg.Body).Message); 
         	  	
         	  	if (message.experience_id==experience) {
         	  	
             		$("#Exhibit").html(title + " "+ message.experience_id, null, 4);
        
					var d;
					if (message.hasOwnProperty('t')) { 
						d = new Date(0); // The 0 there is the key, which sets the date to the epoch
						d.setUTCSeconds(message.t);
					} else {
						d = Date.now(); 
					}
			
					$("#Time").html(d.toString(), null, 4);
			
					//$("#State").html(JSON.stringify(message.state, null, 4));
					var sorted = [];
					var vec; 
					if (message.hasOwnProperty('state')) {
						console.log("emission"); 
						vec = message.state; 
					} else if (message.hasOwnProperty('exposure')) {
						console.log("exposure"); 
						vec = message.exposure; 
					} else {
						console.log("Don't understand the format");
						checking=false;  
						return; 
					}
					for(var key in vec) {
						sorted[sorted.length] = key;
					}
					sorted.sort();
					s='<pre><table width="70%"><tr><td width="5%">&nbsp;</td><td width="1%">&nbsp;</td><td width="44%">&nbsp;</td><td width="25%" align=right><i>intensity</i></td><td width="25%" align=right><i>sentiment</i></td></tr>'; 
					for (const tag of sorted) { 

						s += `<tr><td width="5%" bgcolor="${hashColor(tag)}">&nbsp;</td><td width="1%">&nbsp;</td><td width="44%">#${tag}</td><td width=25% align=right>${vec[tag].intensity.toPrecision(2)}</td><td width=25% align=right>${vec[tag].sentiment.toPrecision(2)}</td>`; 
					}
					s+='</table></pre>';
					$("#State").html(s); 
             	}
         	 	deleteParams.Entries.push( { Id: msg.MessageId, ReceiptHandle: msg.ReceiptHandle } ); 
         	 } 
         
             // change to batch
             sqs.deleteMessageBatch(deleteParams, function(err, data) {
                 checking=false; 
                 if (err) {
                     console.log("Delete Error", err);
                 } else {
                     console.log("Message Deleted", data);
                 }
             });
             
         } else {
         	// No messages 
         }
        checking=false; 
        
     });
     checking=false;
 };


window.setInterval(check, 500);



/* Replace with role with limited permissions for just this action. */

 var params = {
     RoleArn: 'arn:aws:iam::756428767688:role/fssi2019-iam-role-stacy-curious',
     /* required */
     RoleSessionName: 'FerdinandAssumes' /*must be unique?*/
 };

 var sts = new AWS.STS({
     region: "us-west-1",
     accessKeyId: "AKIA3AHVLAHEI4GM26O7",
     secretAccessKey: "",
     DurationSeconds:"43200"  // 12 hours  TODO: auto-renew credentials
 });

$("#Time").html("Assuming role, creating objects.", null, 4);



 sts.assumeRole(params, function(err, data) {
             if (err) {
             	console.log(err, err.stack);
             	return; 
             }// an error occurred


                 AWS.config.update({
                     accessKeyId: data.Credentials.AccessKeyId,
                     secretAccessKey: data.Credentials.SecretAccessKey,
                     sessionToken: data.Credentials.SessionToken
                 });

                 console.log(data); // successful response

                 // Create an SQS service object
                 sqs = new AWS.SQS({ region: "us-west-1" });
                 sns = new AWS.SNS({ region: "us-west-1" });

			
			$("#Time").html("Creating SQS queue.", null, 4);
			 sqs.createQueue(params = {
				 QueueName: queueName,
				 Attributes: { 
				 	ReceiveMessageWaitTimeSeconds: "20", 
				 	MessageRetentionPeriod: "60", 
				 	Policy: SQS_QUEUE_POLICY 
				 	} 
				 }, 
				 function(err,data) { 
                     if (err) {
                         console.log("Create Error", err);
                     } else {
                         console.log("Created", data);
                         queueURL = data.QueueUrl;
							 var params = {
								 TopicArn: "arn:aws:sns:us-west-1:756428767688:" + topic,
								 Protocol: "sqs",
								 Endpoint: "arn:aws:sqs:us-west-1:756428767688:" + queueName
							 };
							 $("#Time").html("Subscribing to topic.", null, 4);
							 sns.subscribe(params, function(err, data) {
								 if (err) console.log(err, err.stack); // an error occurred
								 else {
									 console.log(data); // successful response
									 $("#Time").html("Waiting for SNS message for " + experience + ".", null, 4);
									 ready = true; 
								 }
							 });         
                	}    
                     // Fifo queues incompatible
                     // Have to create with a policy
				
				 });
		          
});
             
             
             
             
             
             
             
             
             
             