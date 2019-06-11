; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"$0.test$fn"(i32 %"arg1", i32 %"arg2") 
{
entry:
  ret i32 %"arg1"
}

define i32 @"$1.main$fn"() 
{
entry:
  %"$0.x$res" = call i32 @"$0.test$fn"(i32 1, i32 2)
  ret i32 %"$0.x$res"
}
