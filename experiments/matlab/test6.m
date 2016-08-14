clear;

bit = 16;
fracbit = 8;
T = mytypes('wfixed',bit,fracbit);
a = 50;
afp = cast(a,'like',T);
b = cast(0,'like',T);
b(:) = afp;

for i = 1:8
	b(:) = b+afp
end;

