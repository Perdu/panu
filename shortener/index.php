<?php
function RandomString()
{
    $characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $randstring = '';
    for ($i = 0; $i < 4; $i++) {
        $randstring .= $characters[rand(0, strlen($characters))];
    }
    return $randstring;
}

function base64url_decode($data) {
    return base64_decode(str_replace(array('-', '_'), array('+', '/'), $data));
}

if (isset($_GET["url"])) {
    $url = base64url_decode($_GET["url"]);
    if (substr($url, 0, 7) == "http://" || substr($url, 0, 8) == "https://") {
	$filename = RandomString();
	$file = fopen($filename, 'w') or die("Unable to create $filename");
	fwrite($file, "<html><head><meta http-equiv='refresh' content='0; URL=\"" . htmlspecialchars($url) . "\"'></head><body></body></html>");
	fclose($file);
	echo $filename;
	return;
    }
}
echo "hi";

?>