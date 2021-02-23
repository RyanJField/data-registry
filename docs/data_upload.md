# How to upload data
There are two steps required to upload data. Firstly you need to request an upload URL. For example:
```
curl -i -X POST -H "Content-Type: application/json" -H "Authorization: token <token>" --data '{"checksum": "<checksum>"}' https://data.scrc.uk/api/data
```
where `<token>` should be replaced with a valid access token and `<checksum>` should be replaced by the SHA-1 checksum of the file you want to upload. The Linux command
`sha1sum` can be used to calculate the SHA-1 checksum

If there are no
existing registered files with the specified checksum you will get a 200 OK response with a JSON body containing a `uuid` and `url`, e.g.
```
{"uuid":"6d77339d-16a1-46b0-9293-5cf3aca298ef","url":"https://..."}
```
The UUID is the unique identifier of the file and should be used as the `path` when creating a `StorageLocation`. The URL can be used to upload the file with a HTTP PUT, e.g.:
```
curl -i --upload-file <filename> "<url>"
```
where <filename> should be replaced with the name of the file you want to upload and `<url>` should be replaced with the URL obtained in the previous step.
