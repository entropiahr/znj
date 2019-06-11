; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

declare i32 @"$0.putchar$external"(i32 %".1") 

define i32 @"$1.main$fn"() 
{
entry:
  %"$res" = call i32 @"$0.putchar$external"(i32 41)
  ret i32 %"$res"
}
