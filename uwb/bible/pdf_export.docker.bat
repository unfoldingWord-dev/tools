cd ../..
docker build . --tag pdf_export --file uwb\bible\pdf_export.Dockerfile 
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
docker run ^
    --rm ^
    --volume %TEMP%:/working ^
    pdf_export -d -c 1 -o /working/output --chunk-divider "<hr\/>"
