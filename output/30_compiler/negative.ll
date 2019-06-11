; ModuleID = ""
target triple = "x86_64-unknown-linux-gnu"
target datalayout = ""

define i32 @"main"() 
{
entry:
  %".ret.1" = add i32 5, -7
  ret i32 %".ret.1"
}
