; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"$0.main$fn"() 
{
entry:
  %"$2.test$res" = add i32 1, 1
  %"$3.test$res" = add i32 1, %"$2.test$res"
  ret i32 %"$3.test$res"
}
