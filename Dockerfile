 # Use AWS Lambda Python runtime as the base image                                          
 FROM public.ecr.aws/lambda/python:3.11                                                     
                                                                                            
 # Set working directory to Lambda task root                                                
 WORKDIR ${LAMBDA_TASK_ROOT}                                                                
                                                                                            
 # Install system dependencies                                                              
 RUN yum -y install gcc gcc-c++ make \                                                      
     libpq-devel \                                                                          
     && yum clean all                                                                       
                                                                                            
 # Copy requirements file                                                                   
 COPY requirements.txt .                                                                    
                                                                                            
 # Install Python dependencies                                                              
 RUN pip install --no-cache-dir -r requirements.txt                                         
                                                                                            
 # Copy the application code                                                                
 COPY . .                                                                                   
                                                                                            
 # Set the Lambda handler                                                                   
 CMD ["main.handler"]
                                                                  
