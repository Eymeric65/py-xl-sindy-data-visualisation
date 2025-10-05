Command to grep the list of process with the elapsed time 

```bask
ps -u eymeric -o pid,etime,cmd | grep python | grep -v grep
```