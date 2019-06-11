; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

declare i32 @"putchar"(i32 %".1") 

define i32 @"main"() 
{
entry:
  %".ret" = call i32 @"putchar"(i32 65)
  ret i32 %".ret"
}
