function d = mydivide(T,a,b)
	if(isscalingunspecified(T))
		d = a/b;
	else
		d = divide(T,a,b);
	end;
	
